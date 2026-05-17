"""LLM outbound port — spec 04, ADR-0002, ADR-0021."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models.rca import RCAHypothesis
from src.domain.models.remediation import RemediationProposal


class LLMPort(ABC):
    """Contract between agent layer and LLM adapter — enforces sanitized=True gate."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        sanitized: bool,
        trace_id: str,
        span_id: str,
    ) -> str:
        """Return LLM completion.

        Raises PiiSanitizationRequired when sanitized is False — ADR-0028.
        Raises LLMOutputInvalid when response fails schema validation — ADR-0021 LLM02.
        """

    @abstractmethod
    async def analyze_rca(
        self,
        incident_id: str,
        context: str,
        *,
        sanitized: bool,
        trace_id: str,
        span_id: str,
    ) -> RCAHypothesis:
        """Return structured RCA hypothesis.

        Raises ConfidenceBelowThreshold when confidence < MIN_CONFIDENCE — ADR-0021 LLM09.
        """

    @abstractmethod
    async def propose_remediation(
        self,
        incident_id: str,
        rca: RCAHypothesis,
        *,
        sanitized: bool,
        trace_id: str,
        span_id: str,
    ) -> RemediationProposal:
        """Return structured remediation proposal."""
