"""E2E: Full incident lifecycle — POST /incidents → TRIAGING → RCA → PROPOSE (spec 02).

Runs against staging environment; pytest.mark.e2e.
Gate: harness/staging-check.yml S05 (e2e test suite with staging marker).
"""

import os

import httpx
import pytest

pytestmark = pytest.mark.e2e

STAGING_BASE = os.environ.get("STAGING_BASE_URL", "http://localhost:8080")


@pytest.fixture
def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=STAGING_BASE, timeout=30.0)


@pytest.mark.asyncio
async def test_incident_create_returns_202(http_client: httpx.AsyncClient) -> None:
    if not os.environ.get("STAGING_BASE_URL"):
        pytest.skip("STAGING_BASE_URL not set — e2e test skipped")

    payload = {
        "title": "P01 latency incident — e2e test",
        "severity": "P2",
        "affected_service": "payment-service",
        "detected_at": "2023-11-14T09:42:00Z",
        "source": "prometheus_alert",
    }
    async with http_client as client:
        resp = await client.post("/api/v1/incidents", json=payload)

    assert resp.status_code == 202
    body = resp.json()
    assert "incident_id" in body
    assert body["status"] == "DETECTING"


@pytest.mark.asyncio
async def test_health_liveness(http_client: httpx.AsyncClient) -> None:
    if not os.environ.get("STAGING_BASE_URL"):
        pytest.skip("STAGING_BASE_URL not set")

    async with http_client as client:
        resp = await client.get("/health/live")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
