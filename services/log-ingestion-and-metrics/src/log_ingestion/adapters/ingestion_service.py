"""Application service: orchestrates LogParser → MetricStorePort for each ingestion call.

Implements IngestionPort (driving port) by parsing validated HAProxy log entries into
MetricPoints across all requested time windows, then persisting them in a single
MetricStorePort.store_batch() call (Spec LIM-01 §3.6 — one pipeline per batch).

Dependency direction: adapters → ports ← domain (ADR-0002). client_ip is never read
from HaproxyLogEntry after this boundary (ADR-0028); LogParser never touches that field.
"""

from __future__ import annotations

from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry
from log_ingestion.domain.models.metric import MetricPoint
from log_ingestion.domain.services.log_parser import LogParser
from log_ingestion.ports.ingestion_port import IngestionPort, _DEFAULT_WINDOWS
from log_ingestion.ports.metric_store_port import MetricStorePort


class IngestionService(IngestionPort):
    """Concrete IngestionPort: parse entries → accumulate MetricPoints → store once.

    One store_batch() call per ingest() invocation keeps write amplification bounded
    and matches the atomicity guarantee in Spec LIM-01 §3.6.
    """

    def __init__(self, store: MetricStorePort, parser: LogParser | None = None) -> None:
        self._store = store
        self._parser = parser if parser is not None else LogParser()

    async def ingest(
        self,
        entries: list[HaproxyLogEntry],
        windows: tuple[int, ...] = _DEFAULT_WINDOWS,
    ) -> None:
        """Parse all entries for all windows into MetricPoints and persist in one batch.

        Args:
            entries: Validated HAProxy log entries. ``client_ip`` is not forwarded
                     to any persistent store (ADR-0028) — LogParser never reads it.
            windows: Bucket sizes in seconds. Defaults to all four supported windows
                     so each entry contributes MetricPoints at every granularity.
        """
        if not entries:
            return

        points: list[MetricPoint] = []
        for entry in entries:
            for window in windows:
                points.extend(self._parser.parse(entry, window))

        await self._store.store_batch(points)
