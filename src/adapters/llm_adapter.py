"""LLM adapter — Anthropic Claude via SDK, sanitized=True gate (ADR-0021, ADR-0028)."""

from __future__ import annotations

import logging
import os

from src.domain.exceptions import LLMOutputInvalid, PiiSanitizationRequired
from src.domain.models.rca import RCAHypothesis
from src.domain.models.remediation import RemediationProposal
from src.guardrails import pii_sanitizer, schema_validator
from src.guardrails.confidence_gate import MIN_CONFIDENCE
from src.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-6"


class LLMAdapter(LLMPort):
    """Calls Anthropic API; enforces PII sanitization gate before every completion."""

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self._model = model
        # API key is read from environment — never stored in source (RULE-C03)
        self._api_key_env = "ANTHROPIC_API_KEY"

    async def complete(
        self,
        prompt: str,
        *,
        sanitized: bool,
        trace_id: str,
        span_id: str,
    ) -> str:
        if not sanitized:
            raise PiiSanitizationRequired(
                "LLMAdapter.complete() called without sanitized=True — ADR-0028"
            )

        import anthropic  # type: ignore[import]

        client = anthropic.AsyncAnthropic(api_key=os.environ[self._api_key_env])
        message = await client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def analyze_rca(
        self,
        incident_id: str,
        context: str,
        *,
        sanitized: bool,
        trace_id: str,
        span_id: str,
    ) -> RCAHypothesis:
        truncated = pii_sanitizer.truncate_for_llm(context)
        raw = await self.complete(truncated, sanitized=sanitized, trace_id=trace_id, span_id=span_id)
        hypothesis = schema_validator.parse_llm_output(raw, RCAHypothesis, context="rca_analysis")
        hypothesis = hypothesis.model_copy(update={"incident_id": incident_id})
        return hypothesis

    async def propose_remediation(
        self,
        incident_id: str,
        rca: RCAHypothesis,
        *,
        sanitized: bool,
        trace_id: str,
        span_id: str,
    ) -> RemediationProposal:
        prompt = pii_sanitizer.truncate_for_llm(
            f"RCA: {rca.root_cause}\nFactors: {rca.contributing_factors}"
        )
        raw = await self.complete(prompt, sanitized=sanitized, trace_id=trace_id, span_id=span_id)
        proposal = schema_validator.parse_llm_output(raw, RemediationProposal, context="remediation_proposal")
        proposal = proposal.model_copy(update={"incident_id": incident_id})
        return proposal
