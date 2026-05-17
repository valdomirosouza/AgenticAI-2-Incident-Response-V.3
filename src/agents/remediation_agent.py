"""RemediationAgent — HITL-gated production action execution (spec 12, ADR-0004, ADR-0023)."""

from __future__ import annotations

import logging

from src.agents.base import BaseAgent
from src.domain.exceptions import BlockedActionError
from src.domain.models.agent_message import AgentMessage, AgentRole
from src.domain.models.remediation import BLOCKED_ACTION_TYPES
from src.ports.audit_port import AuditPort
from src.ports.hitl_port import HITLPort
from src.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)


class RemediationAgent(BaseAgent):
    """Proposes and executes remediation actions under HITL governance.

    Autonomy: HITL — ApprovalToken required for all PRODUCTION_* actions (spec 16 §3.2).
    BLOCKED actions (data_delete, iam_change, firewall_change) are refused at this layer
    before reaching the adapter — defence-in-depth (spec 16 §3.5, ADR-0023).
    """

    role = AgentRole.REMEDIATION

    def __init__(
        self,
        audit_port: AuditPort,
        llm_port: LLMPort,
        hitl_port: HITLPort,
    ) -> None:
        super().__init__(audit_port)
        self._llm = llm_port
        self._hitl = hitl_port

    async def handle(self, message: AgentMessage) -> AgentMessage | None:
        logger.info(
            "remediation_agent_message_received",
            extra={
                "incident_id": message.incident_id,
                "message_type": message.message_type,
            },
        )
        return None

    def _guard_blocked(self, action_type: str) -> None:
        """First-layer BLOCKED check — raises BlockedActionError if action is prohibited."""
        from src.domain.models.remediation import ActionType
        try:
            at = ActionType(action_type)
        except ValueError:
            return
        if at in BLOCKED_ACTION_TYPES:
            raise BlockedActionError(
                f"Action {action_type} is BLOCKED — no approval path exists (spec 16 §3.5)"
            )
