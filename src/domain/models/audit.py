"""Audit trail domain model — spec 17, ADR-0024."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    # Incident lifecycle
    INCIDENT_CREATED = "incident.created"
    INCIDENT_SEVERITY_SET = "incident.severity_set"
    INCIDENT_ESCALATED = "incident.escalated"
    INCIDENT_RESOLVED = "incident.resolved"
    INCIDENT_CLOSED = "incident.closed"
    # RCA
    RCA_HYPOTHESIS_SET = "rca.hypothesis_set"
    RCA_CONFIDENCE_LOW = "rca.confidence_low"
    RCA_REJECTED = "rca.rejected"
    # Remediation
    REMEDIATION_PROPOSED = "remediation.proposed"
    REMEDIATION_APPROVED = "remediation.approved"
    REMEDIATION_REJECTED = "remediation.rejected"
    REMEDIATION_EXECUTED = "remediation.executed"
    REMEDIATION_FAILED = "remediation.failed"
    # HITL
    HITL_APPROVAL_REQUESTED = "hitl.approval_requested"
    HITL_APPROVAL_GRANTED = "hitl.approval_granted"
    HITL_APPROVAL_EXPIRED = "hitl.approval_expired"
    HITL_VALIDATION_FAILED = "hitl.validation_failed"
    # Privacy
    PII_MASKED = "pii.masked"
    # Audit / system
    AUDIT_WRITE_FAILED = "audit.write_failed"
    AUDIT_SECRET_ROTATED = "audit.secret_rotated"
    AUDIT_SUBJECT_ERASURE_COMPLETED = "audit.subject_erasure_completed"
    # Post-mortem
    POSTMORTEM_DRAFTED = "postmortem.drafted"
    POSTMORTEM_PUBLISHED = "postmortem.published"
    # Kill-switch
    AGENT_KILL_SWITCH_ACTIVATED = "agent.kill_switch_activated"


class AuditEvent(BaseModel):
    """Immutable append-only audit event — spec 17 §3.1."""

    record_id: str = Field(description="aud-<date>-<incident_id>-<seq>")
    incident_id: str = Field(description="SYSTEM for non-incident events")
    event_type: AuditEventType
    agent_role: str = Field(
        description="orchestrator | detection | triage | rca | remediation | postmortem"
    )
    action_type: str | None = None
    payload: dict = Field(description="Event-specific data; PII-scrubbed before write")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    timestamp: datetime
    trace_id: str
    span_id: str
    prev_hash: str = Field(description="SHA-256 of previous record; sha256:000…0 for first")
    record_hash: str = Field(
        description="SHA-256(record_id + event_type + timestamp + prev_hash + payload)"
    )


class ChainValidationResult(BaseModel):
    """Result of audit trail hash-chain integrity validation — spec 17 §3.4."""

    incident_id: str
    valid: bool
    record_count: int
    first_broken_link: str | None = None
    validated_at: datetime
