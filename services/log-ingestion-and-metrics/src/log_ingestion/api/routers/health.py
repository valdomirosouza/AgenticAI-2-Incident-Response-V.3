"""Health check endpoints (Spec LIM-02 §3.8).

GET /health/live  — liveness:  always 200; never fails (process is running).
GET /health/ready — readiness: 200 when Redis PING succeeds; 503 otherwise.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from log_ingestion.api.dependencies import get_metric_store
from log_ingestion.ports.metric_store_port import MetricStorePort

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(
    store: Annotated[MetricStorePort, Depends(get_metric_store)],
) -> JSONResponse:
    if await store.ping():
        return JSONResponse({"status": "ready"}, status_code=200)
    return JSONResponse({"status": "not_ready"}, status_code=503)
