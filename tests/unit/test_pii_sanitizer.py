"""Unit tests for src/guardrails/pii_sanitizer.py — ADR-0028, spec 19."""

import pytest

from src.guardrails.pii_sanitizer import sanitize, truncate_for_llm
from tests.fixtures.sample_logs import LOGS_WITH_PII


@pytest.mark.unit
class TestSanitizeFallbackRegex:
    """Tests use the regex fallback path (no Presidio required)."""

    def test_redacts_br_cpf_dotted(self) -> None:
        result = sanitize("cpf: 123.456.789-09", incident_id="INC-TEST")
        assert "123.456.789-09" not in result
        assert "[REDACTED]" in result

    def test_redacts_br_cpf_plain(self) -> None:
        result = sanitize("cpf 12345678909", incident_id="INC-TEST")
        assert "12345678909" not in result

    def test_redacts_email(self) -> None:
        result = sanitize('{"recipient":"user@example.com"}', incident_id="INC-TEST")
        assert "user@example.com" not in result
        assert "[REDACTED]" in result

    def test_redacts_ipv4(self) -> None:
        result = sanitize('connection refused: host="10.0.1.42"', incident_id="INC-TEST")
        assert "10.0.1.42" not in result

    def test_corpus_pii_logs_are_sanitized(self) -> None:
        """Each PII log line from fixture must contain no original PII after sanitize."""
        for line in LOGS_WITH_PII:
            result = sanitize(line)
            assert "123.456.789-09" not in result, f"CPF leaked in: {line}"
            assert "user@example.com" not in result, f"email leaked in: {line}"
            assert "10.0.1.42" not in result, f"IP leaked in: {line}"

    def test_empty_string_returns_empty(self) -> None:
        assert sanitize("") == ""

    def test_none_like_empty_input(self) -> None:
        assert sanitize("   ") == "   "  # whitespace-only — no PII to redact

    def test_clean_text_unchanged(self) -> None:
        text = "payment-service circuit breaker open — no PII here"
        assert sanitize(text) == text


@pytest.mark.unit
class TestTruncateForLlm:
    def test_truncates_at_2000_chars(self) -> None:
        long_text = "a" * 3000
        assert len(truncate_for_llm(long_text)) == 2000

    def test_short_text_unchanged(self) -> None:
        text = "short log line"
        assert truncate_for_llm(text) == text

    def test_exactly_2000_chars_unchanged(self) -> None:
        text = "x" * 2000
        assert truncate_for_llm(text) == text
