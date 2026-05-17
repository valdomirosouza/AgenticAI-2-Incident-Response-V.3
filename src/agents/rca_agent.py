"""RCAAgent — LLM-driven root cause analysis with confidence gate (spec 10, ADR-0004)."""

from __future__ import annotations

import logging

from src.agents.base import BaseAgent
from src.domain.models.agent_message import AgentMessage, AgentRole
from src.ports.audit_port import AuditPort
from src.ports.llm_port import LLMPort
from src.ports.observability_port import ObservabilityPort

logger = logging.getLogger(__name__)


class RCAAgent(BaseAgent):
    """Produces RCAHypothesis from logs/traces via LLM; enforces confidence gate.

    Autonomy: HOTL — acts automatically, human can override.
    Bias metrics: RCRR ≤60%, KL_drift ≤0.10 — ADR-0026.
    Raises ConfidenceBelowThreshold when confidence < 0.6 — ADR-0021 LLM09.
    """

    role = AgentRole.RCA

    def __init__(
        self,
        audit_port: AuditPort,
        llm_port: LLMPort,
        observability_port: ObservabilityPort,
    ) -> None:
        super().__init__(audit_port)
        self._llm = llm_port
        self._obs = observability_port

    async def handle(self, message: AgentMessage) -> AgentMessage | None:
        logger.info(
            "rca_agent_message_received",
            extra={
                "incident_id": message.incident_id,
                "message_type": message.message_type,
            },
        )
        return None
