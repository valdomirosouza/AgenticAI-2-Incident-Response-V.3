"""Unit tests for GET /analytics router (Spec LIM-02 §3.1–§3.6).

Uses httpx.AsyncClient with a stub MetricStorePort injected via dependency_overrides.
All Redis calls are replaced by configurable AsyncMock return values — no network I/O.

Coverage:
  - 200 single-path: traffic, errors, latency, saturation sections present
  - 404 when traffic counter is zero
  - 422 for invalid window and invalid percentiles
  - Signal filtering: only requested section present in response
  - Latency percentile formula (ADR-0035): P50([48,512])=48, P99([48,512])=512
  - RPS formula: total_requests / window_seconds rounded to 2 dp
  - Error rate formulas: 4xx/5xx per traffic
  - Saturation pct: sat_count / traffic × 100
  - Multi-path aggregation: absent trx keys → 404; present keys → aggregated response
  - ZUNIONSTORE temp key deleted after multi-path latency query
  - Custom percentiles query param
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from log_ingestion.api.dependencies import get_metric_store
from log_ingestion.api.routers.analytics import router
from log_ingestion.ports.metric_store_port import MetricStorePort


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_store(
    *,
    traffic: int = 100,
    err4: int = 10,
    err5: int = 2,
    sat: int = 5,
    lat_card: int = 2,
    lat_scores: dict[int, float] | None = None,
    scan_keys: list[str] | None = None,
    union_card: int = 2,
) -> MetricStorePort:
    """Build a stub MetricStorePort with configurable return values."""
    if lat_scores is None:
        lat_scores = {0: 48.0, 1: 512.0}

    store = AsyncMock(spec=MetricStorePort)

    async def _get_counter(key: str) -> int:
        if "trx" in key:
            return traffic
        if "err4" in key:
            return err4
        if "err5" in key:
            return err5
        if "sat" in key:
            return sat
        return 0

    store.get_counter = AsyncMock(side_effect=_get_counter)
    store.get_sorted_set_cardinality = AsyncMock(return_value=lat_card)

    async def _score_at_rank(key: str, rank: int) -> float:
        return lat_scores.get(rank, 0.0)

    store.get_sorted_set_score_at_rank = AsyncMock(side_effect=_score_at_rank)
    store.scan_keys = AsyncMock(return_value=scan_keys or [])
    store.union_sorted_sets_to_temp = AsyncMock(return_value=union_card)
    store.delete_key = AsyncMock()
    return store


def _make_app(store: MetricStorePort) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_metric_store] = lambda: store
    return app


# ── 200 single-path ────────────────────────────────────────────────────────────


class TestSinglePathSuccess:
    @pytest.mark.asyncio
    async def test_returns_200(self) -> None:
        store = _make_store(traffic=100)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_backend_and_path(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web-servers", "path": "/api/v1/orders", "window": "5m"})
        body = r.json()
        assert body["backend"] == "web-servers"
        assert body["path"] == "/api/v1/orders"
        assert body["window"] == "5m"

    @pytest.mark.asyncio
    async def test_all_four_signal_sections_present(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        body = r.json()
        assert "traffic" in body
        assert "errors" in body
        assert "latency_ms" in body
        assert "saturation" in body

    @pytest.mark.asyncio
    async def test_traffic_total_requests(self) -> None:
        store = _make_store(traffic=1842)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        assert r.json()["traffic"]["total_requests"] == 1842

    @pytest.mark.asyncio
    async def test_traffic_rps_formula(self) -> None:
        # 1842 requests / 300 s = 6.14 rps
        store = _make_store(traffic=1842)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        assert r.json()["traffic"]["rps"] == pytest.approx(6.14, abs=0.01)

    @pytest.mark.asyncio
    async def test_error_rates(self) -> None:
        # traffic=1000, err4=10, err5=2 → rate_4xx=0.01, rate_5xx=0.002
        store = _make_store(traffic=1000, err4=10, err5=2)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        errors = r.json()["errors"]
        assert errors["total_4xx"] == 10
        assert errors["total_5xx"] == 2
        assert errors["rate_4xx"] == pytest.approx(0.01, abs=0.0001)
        assert errors["rate_5xx"] == pytest.approx(0.002, abs=0.0001)

    @pytest.mark.asyncio
    async def test_saturation_pct(self) -> None:
        # sat=32, traffic=1000 → 3.2 %
        store = _make_store(traffic=1000, sat=32)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        assert r.json()["saturation"]["high_wait_pct"] == pytest.approx(3.2, abs=0.01)

    @pytest.mark.asyncio
    async def test_latency_p50_two_values(self) -> None:
        # ADR-0035 / Spec LIM-02 §4: P50([48, 512]) → rank=0 → 48.0
        store = _make_store(lat_card=2, lat_scores={0: 48.0, 1: 512.0})
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m", "percentiles": "50"})
        assert r.json()["latency_ms"]["p50"] == pytest.approx(48.0)

    @pytest.mark.asyncio
    async def test_latency_p99_two_values(self) -> None:
        # ADR-0035 / Spec LIM-02 §4: P99([48, 512]) → rank=1 → 512.0
        store = _make_store(lat_card=2, lat_scores={0: 48.0, 1: 512.0})
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m", "percentiles": "99"})
        assert r.json()["latency_ms"]["p99"] == pytest.approx(512.0)

    @pytest.mark.asyncio
    async def test_custom_percentiles_keys_present(self) -> None:
        store = _make_store(lat_card=100, lat_scores={49: 32.0, 94: 145.0, 98: 412.0})
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m", "percentiles": "50,95,99"})
        lat = r.json()["latency_ms"]
        assert "p50" in lat and "p95" in lat and "p99" in lat

    @pytest.mark.asyncio
    async def test_latency_absent_when_no_sorted_set(self) -> None:
        # lat_card=0 → latency_ms must be absent from response
        store = _make_store(traffic=10, lat_card=0)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        assert "latency_ms" not in r.json()


# ── 404 ────────────────────────────────────────────────────────────────────────


class TestNotFound:
    @pytest.mark.asyncio
    async def test_404_when_traffic_zero(self) -> None:
        store = _make_store(traffic=0)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "5m"})
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_404_detail_message(self) -> None:
        store = _make_store(traffic=0)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web-servers", "path": "/api/v1/orders", "window": "5m"})
        assert "web-servers" in r.json()["detail"]
        assert "/api/v1/orders" in r.json()["detail"]

    @pytest.mark.asyncio
    async def test_404_multi_path_no_keys(self) -> None:
        store = _make_store(scan_keys=[])
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "missing", "window": "5m"})
        assert r.status_code == 404


# ── 422 validation ─────────────────────────────────────────────────────────────


class TestValidation:
    @pytest.mark.asyncio
    async def test_invalid_window_returns_422(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "window": "bad"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_backend_returns_422(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"window": "5m"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_percentile_value_returns_422(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "percentiles": "0,50"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_signal_returns_422(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "signal": "bogus"})
        assert r.status_code == 422


# ── signal filtering ───────────────────────────────────────────────────────────


class TestSignalFiltering:
    @pytest.mark.asyncio
    async def test_signal_traffic_only_traffic_present(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "signal": "traffic"})
        body = r.json()
        assert "traffic" in body
        assert "errors" not in body
        assert "latency_ms" not in body
        assert "saturation" not in body

    @pytest.mark.asyncio
    async def test_signal_error_only_errors_present(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "signal": "error"})
        body = r.json()
        assert "errors" in body
        assert "traffic" not in body
        assert "latency_ms" not in body
        assert "saturation" not in body

    @pytest.mark.asyncio
    async def test_signal_latency_only_latency_present(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "signal": "latency"})
        body = r.json()
        assert "latency_ms" in body
        assert "traffic" not in body
        assert "errors" not in body
        assert "saturation" not in body

    @pytest.mark.asyncio
    async def test_signal_saturation_only_saturation_present(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "signal": "saturation"})
        body = r.json()
        assert "saturation" in body
        assert "traffic" not in body
        assert "errors" not in body
        assert "latency_ms" not in body


# ── multi-path aggregation ─────────────────────────────────────────────────────


class TestMultiPathAggregation:
    @pytest.mark.asyncio
    async def test_path_star_in_response(self) -> None:
        store = _make_store(
            traffic=50,
            scan_keys=["lim:trx:web:%2Fapi%2Fa:1718899200", "lim:trx:web:%2Fapi%2Fb:1718899200"],
        )
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            with patch("log_ingestion.api.routers.analytics._current_window_ts", return_value=1718899200):
                r = await client.get("/analytics", params={"backend": "web", "window": "5m"})
        assert r.json()["path"] == "*"

    @pytest.mark.asyncio
    async def test_union_sorted_sets_called_for_multi_path(self) -> None:
        store = _make_store(
            traffic=50,
            scan_keys=["lim:trx:web:%2Fapi%2Fa:1718899200", "lim:trx:web:%2Fapi%2Fb:1718899200"],
        )
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            with patch("log_ingestion.api.routers.analytics._current_window_ts", return_value=1718899200):
                await client.get("/analytics", params={"backend": "web", "window": "5m"})
        store.union_sorted_sets_to_temp.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_temp_key_deleted_after_multi_path_query(self) -> None:
        store = _make_store(
            traffic=50,
            scan_keys=["lim:trx:web:%2Fapi%2Fa:1718899200"],
        )
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            with patch("log_ingestion.api.routers.analytics._current_window_ts", return_value=1718899200):
                await client.get("/analytics", params={"backend": "web", "window": "5m"})
        store.delete_key.assert_awaited_once()


# ── window variants ────────────────────────────────────────────────────────────


class TestWindowVariants:
    @pytest.mark.asyncio
    async def test_1m_window_rps(self) -> None:
        store = _make_store(traffic=60)
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "1m"})
        assert r.json()["traffic"]["rps"] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_1h_window_in_response(self) -> None:
        store = _make_store()
        async with AsyncClient(
            transport=ASGITransport(app=_make_app(store)), base_url="http://test"
        ) as client:
            r = await client.get("/analytics", params={"backend": "web", "path": "/api", "window": "1h"})
        assert r.json()["window"] == "1h"
