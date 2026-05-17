"""Security: PII sanitization gate on LLMAdapter — ADR-0028, OWASP LLM02.

Validates that calling LLMAdapter.complete() without sanitized=True raises
PiiSanitizationRequired — the gate can never be bypassed at the adapter level.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.adapters.llm_adapter import LLMAdapter
from src.domain.exceptions import PiiSanitizationRequired


@pytest.mark.security
class TestPiiSanitizationGate:
    @pytest.mark.asyncio
    async def test_complete_without_sanitized_raises(self) -> None:
        adapter = LLMAdapter()
        with pytest.raises(PiiSanitizationRequired) as exc_info:
            await adapter.complete(
                "analyze this log",
                sanitized=False,
                trace_id="trace-001",
                span_id="span-001",
            )
        assert "sanitized=True" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_with_sanitized_true_reaches_api(self) -> None:
        """Verify the gate passes when sanitized=True; API call is mocked."""
        adapter = LLMAdapter()
        mock_response = AsyncMock()
        mock_response.content = [AsyncMock(text="mocked LLM response")]

        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await adapter.complete(
                "analyze payment-service circuit breaker",
                sanitized=True,
                trace_id="trace-001",
                span_id="span-001",
            )
        assert result == "mocked LLM response"

    @pytest.mark.asyncio
    async def test_pii_containing_prompt_still_blocked_without_flag(self) -> None:
        """Gate fires on sanitized=False regardless of whether prompt contains PII."""
        adapter = LLMAdapter()
        with pytest.raises(PiiSanitizationRequired):
            await adapter.complete(
                "log: cpf=123.456.789-09 error in payment",
                sanitized=False,
                trace_id="trace-002",
                span_id="span-002",
            )
