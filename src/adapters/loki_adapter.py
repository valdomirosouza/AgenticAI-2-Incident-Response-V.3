"""Loki adapter — structured log queries with PII scrubbing at read (spec 05, ADR-0002)."""

from __future__ import annotations

import logging
import os
from datetime import datetime

import httpx

from src.guardrails import pii_sanitizer
from src.ports.observability_port import ObservabilityPort

logger = logging.getLogger(__name__)


class LokiAdapter(ObservabilityPort):
    """Queries Grafana Loki; scrubs PII from log lines before returning (ADR-0028)."""

    def __init__(self) -> None:
        self._base_url = os.environ.get("LOKI_URL", "http://loki:3100")

    async def query_logs(self, service: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        params = {
            "query": f'{{service="{service}"}}',
            "start": int(start.timestamp() * 1e9),
            "end": int(end.timestamp() * 1e9),
            "limit": 500,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._base_url}/loki/api/v1/query_range", params=params)
            resp.raise_for_status()
            lines = resp.json().get("data", {}).get("result", [])

        # Scrub PII from every log line before returning to agent layer
        scrubbed = []
        for stream in lines:
            for ts, line in stream.get("values", []):
                scrubbed.append({"ts": ts, "line": pii_sanitizer.sanitize(line)})
        return scrubbed

    async def query_metrics(self, query: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        return []

    async def query_traces(self, incident_id: str, start: datetime, end: datetime, *, trace_id: str) -> list[dict]:
        return []
