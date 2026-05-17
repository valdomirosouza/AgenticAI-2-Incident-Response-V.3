"""Remediation proposal and ApprovalToken models — spec 02, spec 16, ADR-0023."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    # HOTL actions — no approval needed
    REMEDIATION_PROPOSED = "remediation.proposed"

    # HITL actions — ApprovalToken required (spec 16 §3.2)
    PRODUCTION_POD_RESTART = "PRODUCTION_pod_restart"
    PRODUCTION_CONFIG_CHANGE = "PRODUCTION_config_change"
    PRODUCTION_SCALE_UP = "PRODUCTION_scale_up"
    PRODUCTION_SCALE_DOWN = "PRODUCTION_scale_down"
    PRODUCTION_TRAFFIC_SHIFT = "PRODUCTION_traffic_shift"
    PRODUCTION_DB_QUERY = "PRODUCTION_db_query"
    PRODUCTION_SECRET_ROTATION = "PRODUCTION_secret_rotation"

    # BLOCKED — no approval path exists (spec 16 §3.5)
    PRODUCTION_DATA_DELETE = "PRODUCTION_data_delete"
    PRODUCTION_IAM_CHANGE = "PRODUCTION_iam_change"
    PRODUCTION_FIREWALL_CHANGE = "PRODUCTION_firewall_change"


# Actions that require an ApprovalToken before execution
HITL_ACTION_TYPES: frozenset[ActionType] = frozenset(
    {
        ActionType.PRODUCTION_POD_RESTART,
        ActionType.PRODUCTION_CONFIG_CHANGE,
        ActionType.PRODUCTION_SCALE_UP,
        ActionType.PRODUCTION_SCALE_DOWN,
        ActionType.PRODUCTION_TRAFFIC_SHIFT,
        ActionType.PRODUCTION_DB_QUERY,
        ActionType.PRODUCTION_SECRET_ROTATION,
    }
)

# Actions that are prohibited at all layers — no approval path exists
BLOCKED_ACTION_TYPES: frozenset[ActionType] = frozenset(
    {
        ActionType.PRODUCTION_DATA_DELETE,
        ActionType.PRODUCTION_IAM_CHANGE,
        ActionType.PRODUCTION_FIREWALL_CHANGE,
    }
)


class RemediationProposal(BaseModel):
    """A remediation action proposed by RemediationAgent (requires HITL if PRODUCTION_*)."""

    incident_id: str
    action_type: ActionType
    target_service: str
    parameters: dict = Field(default_factory=dict)
    rationale: str = Field(description="Why this action is proposed (XAI — EU AI Act Art. 13)")
    predicted_effect: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_estimate: str = Field(description="Human-readable risk level: low | medium | high")


class ApprovalToken(BaseModel):
    """Cryptographically signed HITL approval token — ADR-0023."""

    token_id: UUID = Field(default_factory=uuid4)
    incident_id: str
    action_type: ActionType
    approver_role: str
    approved_at: datetime
    expires_at: datetime
    signature: str = Field(
        description="HMAC-SHA256(token_id|incident_id|action_type|approved_at, Vault S-02)"
    )
