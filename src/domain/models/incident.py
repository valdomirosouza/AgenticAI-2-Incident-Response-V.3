"""Canonical Incident domain model — spec 02 §3.1, spec 03."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    P1 = "P1"  # Critical — MTTD target < 5 min, MTTR < 30 min
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low


class IncidentStatus(str, Enum):
    IDLE = "IDLE"
    DETECTING = "DETECTING"
    TRIAGING = "TRIAGING"
    INVESTIGATING = "INVESTIGATING"
    PROPOSING = "PROPOSING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REMEDIATING = "REMEDIATING"
    ESCALATED = "ESCALATED"
    POST_MORTEM = "POST_MORTEM"
    CLOSED = "CLOSED"


class Incident(BaseModel):
    """A detected operational incident driving the Copilot workflow."""

    incident_id: str = Field(
        description="Unique identifier — format: inc-<YYYY-MM-DD>-<seq>"
    )
    title: str
    severity: Severity
    status: IncidentStatus = IncidentStatus.IDLE
    affected_services: list[str] = Field(default_factory=list)
    affected_cujs: list[str] = Field(default_factory=list)
    detected_at: datetime
    resolved_at: datetime | None = None
    trace_id: str = Field(description="W3C TraceContext trace_id for OTel correlation")
    span_id: str = Field(description="W3C TraceContext span_id")

    @property
    def mttd_seconds(self) -> float | None:
        """MTTD in seconds — populated externally from detection event timestamp."""
        return None  # set by DetectionAgent on incident.created

    @property
    def mttr_seconds(self) -> float | None:
        """MTTR in seconds — set when status transitions to CLOSED."""
        if self.resolved_at is None:
            return None
        return (self.resolved_at - self.detected_at).total_seconds()
