"""Driving port: abstract interface for the ingestion use case.

Defines the contract that the POST /ingestion router calls. The concrete implementation
(application service) orchestrates LogParser → MetricStorePort for each validated entry.

References: ADR-0002 (hexagonal), Spec LIM-01 §3.7 (partial-failure semantics).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry

_DEFAULT_WINDOWS: tuple[int, ...] = (60, 300, 900, 3600)
_MAX_ERROR_STRINGS: int = 10


@dataclass(frozen=True)
class IngestionResult:
    """Outcome of a single ingestion call (Spec LIM-01 §3.7 response body).

    ``errors`` contains at most ``_MAX_ERROR_STRINGS`` strings to cap response size.
    """

    accepted: int
    rejected: int
    errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.accepted < 0:
            raise ValueError("accepted must be non-negative")
        if self.rejected < 0:
            raise ValueError("rejected must be non-negative")
        if len(self.errors) > _MAX_ERROR_STRINGS:
            raise ValueError(f"errors must contain at most {_MAX_ERROR_STRINGS} strings")


class IngestionPort(ABC):
    """Primary (driving) port: ingestion use-case boundary called by the API router.

    The implementation receives already-validated HaproxyLogEntry objects and is
    responsible for parsing them into MetricPoints and persisting them via MetricStorePort.
    Partial-failure semantics (accepted/rejected counts) are handled by the router, which
    pre-validates each raw entry and calls this port only with the valid subset.
    """

    @abstractmethod
    async def ingest(
        self,
        entries: list[HaproxyLogEntry],
        windows: tuple[int, ...] = _DEFAULT_WINDOWS,
    ) -> None:
        """Parse ``entries`` into MetricPoints and persist them for all ``windows``.

        Called once per batch after the router has filtered out invalid entries.
        Raises MetricStoreError if the underlying store write fails; callers should
        translate this to lim_ingestion_events_total{result="store_error"}.

        Args:
            entries: Validated HAProxy log entries. ``client_ip`` must not be forwarded
                     to any persistent store (ADR-0028).
            windows: Bucket sizes in seconds to write to. Defaults to all four supported
                     windows so each MetricPoint is stored at every granularity.
        """
