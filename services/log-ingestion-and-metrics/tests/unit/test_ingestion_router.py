"""Unit tests for POST /ingestion router (Spec LIM-01 §3.7).

Uses httpx.AsyncClient with dependency overrides to inject stub IngestionPort.
No Redis or real parser involved — tests cover HTTP contract and partial-failure logic.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from log_ingestion.api.dependencies import get_ingestion_service
from log_ingestion.api.routers.ingestion import router
from log_ingestion.ports.ingestion_port import IngestionPort

# ── canonical valid entry dict (Spec LIM-01 §3.1) ─────────────────────────────

_VALID: dict[str, Any] = {
    "timestamp": "2024-06-20T15:56:09",
    "client_ip": "192.168.1.50",
    "client_port": 44321,
    "frontend": "http-in",
    "backend": "web-servers",
    "server": "web-01",
    "status_code": 200,
    "bytes_read": 1450,
    "request": "GET /api/v1/data HTTP/1.1",
    "termination_state": "--",
    "timers": {"total_time": 105, "wait": 2, "connect": 1, "response": 102},
}

_INVALID: dict[str, Any] = {"timestamp": "bad-date", "status_code": -1}


# ── test app fixture ───────────────────────────────────────────────────────────


@pytest.fixture
def stub_svc() -> IngestionPort:
    svc = AsyncMock(spec=IngestionPort)
    svc.ingest = AsyncMock(return_value=None)
    return svc


@pytest.fixture
def app(stub_svc: IngestionPort) -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_ingestion_service] = lambda: stub_svc
    return test_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ── single entry (object body) ─────────────────────────────────────────────────


class TestSingleEntry:
    @pytest.mark.asyncio
    async def test_valid_single_entry_returns_202(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=_VALID)
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_valid_single_entry_accepted_1(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=_VALID)
        assert response.json()["accepted"] == 1
        assert response.json()["rejected"] == 0
        assert response.json()["errors"] == []

    @pytest.mark.asyncio
    async def test_invalid_single_entry_rejected_1(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=_INVALID)
        body = response.json()
        assert response.status_code == 202
        assert body["accepted"] == 0
        assert body["rejected"] == 1
        assert len(body["errors"]) == 1


# ── batch (array body) ─────────────────────────────────────────────────────────


class TestBatch:
    @pytest.mark.asyncio
    async def test_batch_3_valid_accepted_3(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=[_VALID, _VALID, _VALID])
        body = response.json()
        assert response.status_code == 202
        assert body["accepted"] == 3
        assert body["rejected"] == 0

    @pytest.mark.asyncio
    async def test_mixed_batch_partial_failure(self, client: AsyncClient) -> None:
        # [valid, invalid, valid] → accepted=2, rejected=1
        response = await client.post("/ingestion", json=[_VALID, _INVALID, _VALID])
        body = response.json()
        assert body["accepted"] == 2
        assert body["rejected"] == 1
        assert len(body["errors"]) == 1

    @pytest.mark.asyncio
    async def test_empty_batch_accepted_0(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=[])
        body = response.json()
        assert response.status_code == 202
        assert body["accepted"] == 0
        assert body["rejected"] == 0

    @pytest.mark.asyncio
    async def test_batch_1001_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=[_VALID] * 1001)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_exactly_1000_processed(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=[_VALID] * 1000)
        body = response.json()
        assert response.status_code == 202
        assert body["accepted"] == 1000


# ── error list capping ─────────────────────────────────────────────────────────


class TestErrorCapping:
    @pytest.mark.asyncio
    async def test_errors_capped_at_10(self, client: AsyncClient) -> None:
        # 15 invalid entries → errors list has at most 10 strings
        response = await client.post("/ingestion", json=[_INVALID] * 15)
        body = response.json()
        assert body["rejected"] == 15
        assert len(body["errors"]) == 10

    @pytest.mark.asyncio
    async def test_errors_empty_when_all_valid(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=[_VALID, _VALID])
        assert response.json()["errors"] == []


# ── ingest delegation ──────────────────────────────────────────────────────────


class TestIngestionDelegation:
    @pytest.mark.asyncio
    async def test_ingest_called_with_valid_entries_only(
        self, client: AsyncClient, stub_svc: IngestionPort
    ) -> None:
        await client.post("/ingestion", json=[_VALID, _INVALID, _VALID])
        call_args = stub_svc.ingest.call_args
        entries_passed = call_args[0][0]
        assert len(entries_passed) == 2

    @pytest.mark.asyncio
    async def test_ingest_called_once_per_request(
        self, client: AsyncClient, stub_svc: IngestionPort
    ) -> None:
        await client.post("/ingestion", json=[_VALID, _VALID])
        assert stub_svc.ingest.await_count == 1

    @pytest.mark.asyncio
    async def test_client_ip_absent_from_response(self, client: AsyncClient) -> None:
        response = await client.post("/ingestion", json=_VALID)
        body_str = response.text
        assert "192.168.1.50" not in body_str


# ── error message content ──────────────────────────────────────────────────────


class TestErrorMessages:
    @pytest.mark.asyncio
    async def test_error_string_references_entry_index(
        self, client: AsyncClient
    ) -> None:
        # Second entry (index 1) is invalid
        response = await client.post("/ingestion", json=[_VALID, _INVALID])
        body = response.json()
        assert "entry 1" in body["errors"][0]
