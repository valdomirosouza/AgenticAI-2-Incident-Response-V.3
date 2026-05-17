"""Base agent — shared tracing, audit, and logging scaffolding (ADR-0004)."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from src.domain.models.agent_message import AgentMessage, AgentRole
from src.domain.models.audit import AuditEvent, AuditEventType
from src.ports.audit_port import AuditPort


class BaseAgent(ABC):
    """Common base for all six specialist agents."""

    role: AgentRole

    def __init__(self, audit_port: AuditPort) -> None:
        self._audit = audit_port
        self._log = logging.getLogger(f"agents.{self.role.value}")

    @abstractmethod
    async def handle(self, message: AgentMessage) -> AgentMessage | None:
        """Process inbound message and return optional outbound message."""

    async def _emit(
        self,
        *,
        record_id: str,
        incident_id: str,
        event_type: AuditEventType,
        action_type: str | None = None,
        payload: dict,
        confidence: float | None = None,
        trace_id: str,
        span_id: str,
        prev_hash: str,
        record_hash: str,
    ) -> None:
        event = AuditEvent(
            record_id=record_id,
            incident_id=incident_id,
            event_type=event_type,
            agent_role=self.role.value,
            action_type=action_type,
            payload=payload,
            confidence=confidence,
            timestamp=datetime.now(tz=timezone.utc),
            trace_id=trace_id,
            span_id=span_id,
            prev_hash=prev_hash,
            record_hash=record_hash,
        )
        await self._audit.append(event)
