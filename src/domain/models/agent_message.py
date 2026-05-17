"""Inter-agent message schema — spec 02 §3.4."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    DETECTION = "detection_agent"
    TRIAGE = "triage_agent"
    RCA = "rca_agent"
    REMEDIATION = "remediation_agent"
    POSTMORTEM = "postmortem_agent"


class MessageType(str, Enum):
    ANALYZE = "ANALYZE"
    TRIAGE = "TRIAGE"
    RCA = "RCA"
    PROPOSE = "PROPOSE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DRAFT = "DRAFT"


class AgentMessage(BaseModel):
    """Typed inter-agent message — spec 02 §3.4."""

    message_id: UUID = Field(default_factory=uuid4)
    incident_id: str
    source_agent: AgentRole
    target_agent: AgentRole
    message_type: MessageType
    payload: dict  # validated against message_type-specific schema by receiver
    trace_id: str = Field(description="W3C TraceContext trace_id — propagated from request")
    span_id: str = Field(description="W3C TraceContext span_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Required for PROPOSE and RCA message types",
    )
