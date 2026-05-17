"""Audit outbound port — spec 17, ADR-0002, ADR-0024."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models.audit import AuditEvent, ChainValidationResult


class AuditPort(ABC):
    """Contract for append-only audit trail writes and hash-chain validation."""

    @abstractmethod
    async def append(self, event: AuditEvent) -> None:
        """Append audit event to WORM storage.

        Raises AuditWriteFailure on any write error — triggers kill-switch (ADR-0025).
        """

    @abstractmethod
    async def validate_chain(self, incident_id: str) -> ChainValidationResult:
        """Validate SHA-256 hash chain for all events under incident_id."""

    @abstractmethod
    async def get_events(self, incident_id: str) -> list[AuditEvent]:
        """Return all audit events for incident_id in append order."""
