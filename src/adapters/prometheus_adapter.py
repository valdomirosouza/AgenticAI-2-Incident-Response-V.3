"""Prometheus adapter — Golden Signals metrics queries (spec 06, ADR-0002)."""

from __future__ import annotations

import logging
import os
from datetime import datetime

import httpx

from src.ports.observability_port import ObservabilityPort

logger = logging.getLogger(__name__)


class PrometheusAdapter(ObservabilityPort):
    """Queries Prometheus HTTP API for metrics data."""

    def __init__(self) -> None:
        self._base_url = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")

    async def query_logs(self, service: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        # Logs sourced from Loki, not Prometheus — delegate to LokiAdapter
        return []

    async def query_metrics(self, query: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        params = {
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": "60s",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._base_url}/api/v1/query_range", params=params)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("result", [])

    async def query_traces(self, incident_id: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        # Traces sourced from Tempo — delegate to TempoAdapter
        return []
