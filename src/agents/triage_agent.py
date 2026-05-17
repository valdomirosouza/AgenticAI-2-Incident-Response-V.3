"""TriageAgent — HOTL severity classification with bias guardrails (spec 08, ADR-0004)."""

from __future__ import annotations

import logging

from src.agents.base import BaseAgent
from src.domain.models.agent_message import AgentMessage, AgentRole
from src.domain.models.incident import Severity
from src.ports.audit_port import AuditPort
from src.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)


class TriageAgent(BaseAgent):
    """Classifies incident severity P1–P4; monitors SCER and CV_MTTD bias metrics.

    Autonomy: HOTL — acts automatically, human can override (spec 16 §3.1).
    Bias metrics: SCER ≤10% overall, CV_MTTD ≤0.30 — ADR-0026.
    """

    role = AgentRole.TRIAGE

    def __init__(
        self,
        audit_port: AuditPort,
        llm_port: LLMPort,
    ) -> None:
        super().__init__(audit_port)
        self._llm = llm_port

    async def handle(self, message: AgentMessage) -> AgentMessage | None:
        logger.info(
            "triage_agent_message_received",
            extra={
                "incident_id": message.incident_id,
                "message_type": message.message_type,
            },
        )
        return None
