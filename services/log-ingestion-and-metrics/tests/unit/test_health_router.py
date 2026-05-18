"""Unit tests for GET /health/live and GET /health/ready (Spec LIM-02 §3.8).

Uses httpx.AsyncClient with dependency overrides so no Redis connection is needed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from log_ingestion.api.dependencies import get_metric_store
from log_ingestion.api.routers.health import router
from log_ingestion.ports.metric_store_port import MetricStorePort


# ── test app fixture ───────────────────────────────────────────────────────────


def _make_app(ping_result: bool) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    stub_store = AsyncMock(spec=MetricStorePort)
    stub_store.ping = AsyncMock(return_value=ping_result)
    app.dependency_overrides[get_metric_store] = lambda: stub_store
    return app


@pytest.fixture
def ready_app() -> FastAPI:
    return _make_app(ping_result=True)


@pytest.fixture
def not_ready_app() -> FastAPI:
    return _make_app(ping_result=False)


# ── GET /health/live ───────────────────────────────────────────────────────────


class TestLiveness:
    @pytest.mark.asyncio
    async def test_liveness_returns_200(self, ready_app: FastAPI) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=ready_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_liveness_body(self, ready_app: FastAPI) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=ready_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
        assert response.json() == {"status": "alive"}

    @pytest.mark.asyncio
    async def test_liveness_200_even_when_redis_down(self, not_ready_app: FastAPI) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=not_ready_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
        assert response.status_code == 200


# ── GET /health/ready ──────────────────────────────────────────────────────────


class TestReadiness:
    @pytest.mark.asyncio
    async def test_readiness_200_when_ping_true(self, ready_app: FastAPI) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=ready_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_readiness_body_ready(self, ready_app: FastAPI) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=ready_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
        assert response.json() == {"status": "ready"}

    @pytest.mark.asyncio
    async def test_readiness_503_when_ping_false(self, not_ready_app: FastAPI) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=not_ready_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_readiness_body_not_ready(self, not_ready_app: FastAPI) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=not_ready_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
        assert response.json() == {"status": "not_ready"}
