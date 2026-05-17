"""OrchestratorAgent — state machine driver for the incident lifecycle (spec 02, ADR-0004)."""

from __future__ import annotations

import logging
from enum import Enum

from src.agents.base import BaseAgent
from src.domain.models.agent_message import AgentMessage, AgentRole, MessageType
from src.domain.models.incident import IncidentStatus
from src.ports.audit_port import AuditPort

logger = logging.getLogger(__name__)


class OrchestratorState(str, Enum):
    """Internal state machine — mirrors IncidentStatus with pending-approval split."""

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


class OrchestratorAgent(BaseAgent):
    """Routes messages between specialist agents; drives incident state machine.

    Valid transitions (spec 02 §3.3):
      IDLE → DETECTING → TRIAGING → INVESTIGATING →
      PROPOSING → PENDING_APPROVAL → REMEDIATING → POST_MORTEM → CLOSED
      Any state → ESCALATED (on ConfidenceBelowThreshold or HITL timeout)
    """

    role = AgentRole.ORCHESTRATOR

    def __init__(self, audit_port: AuditPort) -> None:
        super().__init__(audit_port)
        self._state = OrchestratorState.IDLE

    @property
    def state(self) -> OrchestratorState:
        return self._state

    async def handle(self, message: AgentMessage) -> AgentMessage | None:
        logger.info(
            "orchestrator_message_received",
            extra={
                "incident_id": message.incident_id,
                "message_type": message.message_type,
                "source_agent": message.source_agent,
                "state": self._state,
            },
        )
        # Routing logic implemented per spec 02 §3.4 in adapter layer
        return None
