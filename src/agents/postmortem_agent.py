"""PostMortemAgent — automated post-mortem drafting (spec 14, ADR-0004)."""

from __future__ import annotations

import logging

from src.agents.base import BaseAgent
from src.domain.models.agent_message import AgentMessage, AgentRole
from src.ports.audit_port import AuditPort
from src.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)


class PostMortemAgent(BaseAgent):
    """Drafts blameless post-mortem from incident timeline and audit trail.

    Autonomy: HOTL — draft is reviewed and approved by human before publishing.
    XAI requirement: explanation field mandatory in all LLM outputs (EU AI Act Art. 13).
    """

    role = AgentRole.POSTMORTEM

    def __init__(
        self,
        audit_port: AuditPort,
        llm_port: LLMPort,
    ) -> None:
        super().__init__(audit_port)
        self._llm = llm_port

    async def handle(self, message: AgentMessage) -> AgentMessage | None:
        logger.info(
            "postmortem_agent_message_received",
            extra={
                "incident_id": message.incident_id,
                "message_type": message.message_type,
            },
        )
        return None
