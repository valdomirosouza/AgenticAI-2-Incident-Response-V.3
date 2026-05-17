"""DetectionAgent — HOTL Golden Signals anomaly detection (spec 03, ADR-0004)."""

from __future__ import annotations

import logging

from src.agents.base import BaseAgent
from src.domain.models.agent_message import AgentMessage, AgentRole, MessageType
from src.ports.audit_port import AuditPort
from src.ports.observability_port import ObservabilityPort

logger = logging.getLogger(__name__)


class DetectionAgent(BaseAgent):
    """Monitors Golden Signals; raises ANALYZE message to orchestrator on anomaly.

    Autonomy: HOTL — acts automatically, human can override (spec 16 §3.1).
    """

    role = AgentRole.DETECTION

    def __init__(
        self,
        audit_port: AuditPort,
        observability_port: ObservabilityPort,
    ) -> None:
        super().__init__(audit_port)
        self._obs = observability_port

    async def handle(self, message: AgentMessage) -> AgentMessage | None:
        logger.info(
            "detection_agent_message_received",
            extra={
                "incident_id": message.incident_id,
                "message_type": message.message_type,
            },
        )
        return None
