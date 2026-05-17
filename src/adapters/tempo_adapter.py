"""Tempo adapter — distributed trace queries (spec 07, ADR-0002)."""

from __future__ import annotations

import logging
import os
from datetime import datetime

import httpx

from src.ports.observability_port import ObservabilityPort

logger = logging.getLogger(__name__)


class TempoAdapter(ObservabilityPort):
    """Queries Grafana Tempo for distributed traces correlated to incident_id."""

    def __init__(self) -> None:
        self._base_url = os.environ.get("TEMPO_URL", "http://tempo:3200")

    async def query_logs(self, service: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        return []

    async def query_metrics(self, query: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        return []

    async def query_traces(self, incident_id: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        params = {
            "tags": f"incident_id={incident_id}",
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "limit": 100,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._base_url}/api/search", params=params)
            resp.raise_for_status()
            return resp.json().get("traces", [])
