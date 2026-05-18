"""Integration tests — full POST /ingestion → Redis → GET /analytics pipeline.

No mocks: real IngestionService, real RedisMetricAdapter, real analytics router,
all wired together against an in-process FakeRedis instance.
This verifies end-to-end correctness of the metric storage and retrieval path
without requiring a live Redis container.

Coverage:
  - Round-trip: ingest entries → analytics returns correct counters and rps
  - Error rate: 4xx and 5xx errors reflected in analytics.errors section
  - Saturation: high-wait entries counted correctly
  - Latency percentiles: P50/P99 over a known distribution
  - Signal filtering: ?signal=traffic returns only traffic section
  - Multi-path aggregation: two paths summed in aggregate query
  - 404 when no data exists for the requested backend/window
  - Partial failure: only accepted entries reach the store

References: Spec LIM-01 §3.7, Spec LIM-02 §3.1–§3.6, ADR-0034, ADR-0035
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime

import fakeredis.aioredis
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from log_ingestion.adapters.ingestion_service import IngestionService
from log_ingestion.adapters.redis_metric_adapter import RedisMetricAdapter
from log_ingestion.api.dependencies import get_ingestion_service, get_metric_store
from log_ingestion.api.routers import analytics, health, ingestion
from log_ingestion.domain.services.log_parser import LogParser


# ── Shared fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
async def fake_redis() -> fakeredis.aioredis.FakeRedis:
    """Isolated in-process FakeRedis — no network required."""
    return fakeredis.aioredis.FakeRedis(decode_responses=False)


@pytest.fixture
async def metric_store(fake_redis: fakeredis.aioredis.FakeRedis) -> RedisMetricAdapter:
    return RedisMetricAdapter(fake_redis)


@pytest.fixture
async def ingestion_svc(metric_store: RedisMetricAdapter) -> IngestionService:
    return IngestionService(store=metric_store, parser=LogParser(sat_threshold_ms=50))


@pytest.fixture
def app(metric_store: RedisMetricAdapter, ingestion_svc: IngestionService) -> FastAPI:
    _app = FastAPI()
    _app.include_router(ingestion.router)
    _app.include_router(analytics.router)
    _app.include_router(health.router)
    _app.dependency_overrides[get_metric_store] = lambda: metric_store
    _app.dependency_overrides[get_ingestion_service] = lambda: ingestion_svc
    return _app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _now_ts() -> str:
    """Current local time as a timestamp string matching HaproxyLogEntry.timestamp format.

    LogParser._window_ts calls datetime.timestamp() which treats naive datetimes as local
    time, matching the epoch returned by time.time(). Using datetime.now() (naive local)
    ensures the stored window_ts equals the current-window query in the analytics router.
    """
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _entry(**overrides: object) -> dict:
    """Canonical valid log entry in the current time window."""
    base: dict = {
        "timestamp": _now_ts(),
        "client_ip": "10.0.0.1",
        "client_port": 44321,
        "frontend": "http-in",
        "backend": "web-servers",
        "server": "web-01",
        "status_code": 200,
        "bytes_read": 1450,
        "request": "GET /api/v1/health HTTP/1.1",
        "termination_state": "--",
        "timers": {"total_time": 30, "wait": 5, "connect": 1, "response": 24},
    }
    base.update(overrides)
    return base


# ── Round-trip: traffic and RPS ────────────────────────────────────────────────


@pytest.mark.integration
async def test_ingest_then_analytics_returns_traffic(client: AsyncClient) -> None:
    entries = [_entry(), _entry(), _entry()]
    resp = await client.post("/ingestion", json=entries)
    assert resp.status_code == 202
    assert resp.json()["accepted"] == 3

    r = await client.get("/analytics", params={"backend": "web-servers", "window": "1m"})
    assert r.status_code == 200
    data = r.json()
    assert data["traffic"]["total_requests"] == 3
    assert data["traffic"]["rps"] == round(3 / 60, 2)


@pytest.mark.integration
async def test_analytics_404_when_no_data(client: AsyncClient) -> None:
    r = await client.get("/analytics", params={"backend": "no-such-backend", "window": "1m"})
    assert r.status_code == 404


# ── Error rate round-trip ──────────────────────────────────────────────────────


@pytest.mark.integration
async def test_error_rates_round_trip(client: AsyncClient) -> None:
    entries = [
        _entry(),
        _entry(status_code=404),
        _entry(status_code=404),
        _entry(status_code=503),
    ]
    resp = await client.post("/ingestion", json=entries)
    assert resp.json()["accepted"] == 4

    r = await client.get("/analytics", params={"backend": "web-servers", "window": "1m"})
    assert r.status_code == 200
    errors = r.json()["errors"]
    assert errors["total_4xx"] == 2
    assert errors["total_5xx"] == 1
    assert errors["rate_4xx"] == round(2 / 4, 4)
    assert errors["rate_5xx"] == round(1 / 4, 4)


# ── Saturation round-trip ─────────────────────────────────────────────────────


@pytest.mark.integration
async def test_saturation_round_trip(client: AsyncClient) -> None:
    # 2 high-wait (>50 ms threshold) out of 4 total → 50.0 %
    high_wait_timers = {"total_time": 200, "wait": 80, "connect": 1, "response": 119}
    entries = [_entry(), _entry(), _entry(timers=high_wait_timers), _entry(timers=high_wait_timers)]
    await client.post("/ingestion", json=entries)

    r = await client.get("/analytics", params={"backend": "web-servers", "window": "1m"})
    assert r.status_code == 200
    assert r.json()["saturation"]["high_wait_pct"] == 50.0


# ── Latency percentile round-trip ─────────────────────────────────────────────


@pytest.mark.integration
async def test_latency_p50_p99_round_trip(client: AsyncClient) -> None:
    # Two entries: total_time=30 ms and total_time=200 ms (LogParser uses total_time)
    slow_timers = {"total_time": 200, "wait": 80, "connect": 1, "response": 119}
    entries = [_entry(), _entry(timers=slow_timers)]
    await client.post("/ingestion", json=entries)

    r = await client.get(
        "/analytics",
        params={"backend": "web-servers", "window": "1m", "percentiles": "50,99"},
    )
    assert r.status_code == 200
    lat = r.json()["latency_ms"]
    assert "p50" in lat and "p99" in lat
    # 2-element sorted set [30, 200]:
    #   P50: rank = max(0, ceil(0.50×2)−1) = 0 → 30
    #   P99: rank = max(0, ceil(0.99×2)−1) = 1 → 200
    assert lat["p50"] == 30.0
    assert lat["p99"] == 200.0


# ── Signal filtering ──────────────────────────────────────────────────────────


@pytest.mark.integration
async def test_signal_filter_traffic_only(client: AsyncClient) -> None:
    await client.post("/ingestion", json=[_entry()])

    r = await client.get(
        "/analytics",
        params={"backend": "web-servers", "window": "1m", "signal": "traffic"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "traffic" in data
    assert "errors" not in data
    assert "latency_ms" not in data
    assert "saturation" not in data


@pytest.mark.integration
async def test_signal_filter_error_only(client: AsyncClient) -> None:
    await client.post("/ingestion", json=[_entry(status_code=503)])

    r = await client.get(
        "/analytics",
        params={"backend": "web-servers", "window": "1m", "signal": "error"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "errors" in data
    assert "traffic" not in data
    assert "saturation" not in data


# ── Multi-path aggregation ────────────────────────────────────────────────────


@pytest.mark.integration
async def test_multi_path_aggregation_totals(client: AsyncClient) -> None:
    # 2 requests to /api/v1/health, 3 to /api/v1/orders
    path_b = "GET /api/v1/orders HTTP/1.1"
    entries = [
        _entry(), _entry(),
        _entry(request=path_b), _entry(request=path_b), _entry(request=path_b),
    ]
    await client.post("/ingestion", json=entries)

    r = await client.get("/analytics", params={"backend": "web-servers", "window": "1m"})
    assert r.status_code == 200
    data = r.json()
    assert data["path"] == "*"
    assert data["traffic"]["total_requests"] == 5


@pytest.mark.integration
async def test_single_path_isolation_from_other_paths(client: AsyncClient) -> None:
    path_b = "GET /api/v1/orders HTTP/1.1"
    entries = [
        _entry(), _entry(),
        _entry(request=path_b), _entry(request=path_b), _entry(request=path_b),
    ]
    await client.post("/ingestion", json=entries)

    r = await client.get(
        "/analytics",
        params={"backend": "web-servers", "window": "1m", "path": "/api/v1/health"},
    )
    assert r.status_code == 200
    assert r.json()["traffic"]["total_requests"] == 2


# ── Partial failure does not corrupt store ────────────────────────────────────


@pytest.mark.integration
async def test_partial_failure_accepted_entries_stored(client: AsyncClient) -> None:
    bad = {"not": "valid"}
    entries = [_entry(), bad, _entry()]
    resp = await client.post("/ingestion", json=entries)
    assert resp.status_code == 202
    body = resp.json()
    assert body["accepted"] == 2
    assert body["rejected"] == 1

    r = await client.get("/analytics", params={"backend": "web-servers", "window": "1m"})
    assert r.status_code == 200
    assert r.json()["traffic"]["total_requests"] == 2
