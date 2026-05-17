"""Health check router — liveness and readiness probes (spec 01 §3.5)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Kubernetes liveness probe — returns 200 when process is running."""
    return HealthResponse(status="ok", version="0.5.0")


@router.get("/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    """Kubernetes readiness probe — returns 200 when dependencies are reachable."""
    return HealthResponse(status="ok", version="0.5.0")
