"""Observability outbound port — spec 05, spec 06, spec 07, ADR-0002."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class ObservabilityPort(ABC):
    """Contract for reading logs, metrics, and traces from the observability stack."""

    @abstractmethod
    async def query_logs(
        self,
        service: str,
        start: datetime,
        end: datetime,
        *,
        trace_id: str,
    ) -> list[dict]:
        """Return structured log lines for service in time window (PII-scrubbed)."""

    @abstractmethod
    async def query_metrics(
        self,
        query: str,
        start: datetime,
        end: datetime,
        *,
        trace_id: str,
    ) -> list[dict]:
        """Return Prometheus instant/range vector result."""

    @abstractmethod
    async def query_traces(
        self,
        incident_id: str,
        start: datetime,
        end: datetime,
        *,
        trace_id: str,
    ) -> list[dict]:
        """Return Tempo trace spans correlated to incident_id."""
