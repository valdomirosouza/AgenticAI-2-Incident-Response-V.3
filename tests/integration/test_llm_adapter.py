"""Integration tests for LLMAdapter — requires ANTHROPIC_API_KEY in environment.

These tests are skipped in CI unless the `integration` marker is selected explicitly.
Gate: harness/staging-check.yml S04 (prompt injection + LLM behaviour tests).
"""

import os

import pytest

from src.adapters.llm_adapter import LLMAdapter
from src.domain.exceptions import PiiSanitizationRequired
from src.guardrails.pii_sanitizer import sanitize, truncate_for_llm
from tests.fixtures.sample_logs import LOGS_P04_AVAILABILITY


pytestmark = pytest.mark.integration


@pytest.fixture
def adapter() -> LLMAdapter:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — integration test skipped")
    return LLMAdapter()


@pytest.mark.asyncio
async def test_sanitized_completion_returns_string(adapter: LLMAdapter) -> None:
    log_ctx = truncate_for_llm(sanitize("\n".join(LOGS_P04_AVAILABILITY)))
    result = await adapter.complete(
        f"Summarize this incident log in one sentence: {log_ctx}",
        sanitized=True,
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="00f067aa0ba902b7",
    )
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_unsanitized_call_raises_gate(adapter: LLMAdapter) -> None:
    with pytest.raises(PiiSanitizationRequired):
        await adapter.complete(
            "cpf: 123.456.789-09",
            sanitized=False,
            trace_id="trace-integ-001",
            span_id="span-001",
        )
