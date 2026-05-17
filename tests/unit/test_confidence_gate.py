"""Unit tests for src/guardrails/confidence_gate.py — ADR-0021 LLM09."""

import pytest

from src.domain.exceptions import ConfidenceBelowThreshold
from src.guardrails.confidence_gate import MIN_CONFIDENCE, enforce, label_if_low


@pytest.mark.unit
class TestEnforce:
    def test_raises_when_below_threshold(self) -> None:
        with pytest.raises(ConfidenceBelowThreshold) as exc_info:
            enforce(0.5, context="rca_analysis", incident_id="INC-TEST-001")
        assert "LOW CONFIDENCE: 50%" in str(exc_info.value)

    def test_raises_at_exactly_min_minus_epsilon(self) -> None:
        with pytest.raises(ConfidenceBelowThreshold):
            enforce(MIN_CONFIDENCE - 0.001, context="test", incident_id="INC-TEST-001")

    def test_passes_at_threshold(self) -> None:
        enforce(MIN_CONFIDENCE, context="test", incident_id="INC-TEST-001")  # must not raise

    def test_passes_above_threshold(self) -> None:
        enforce(0.97, context="rca_analysis", incident_id="INC-P04-001")  # corpus P04

    def test_error_message_contains_incident_id_context(self) -> None:
        with pytest.raises(ConfidenceBelowThreshold) as exc_info:
            enforce(0.54, context="multi_hop_rca", incident_id="INC-P12-001")
        msg = str(exc_info.value)
        assert "54%" in msg
        assert "multi_hop_rca" in msg

    def test_zero_confidence_raises(self) -> None:
        with pytest.raises(ConfidenceBelowThreshold):
            enforce(0.0, context="test", incident_id="INC-TEST-001")


@pytest.mark.unit
class TestLabelIfLow:
    def test_prepends_prefix_below_threshold(self) -> None:
        result = label_if_low(0.54, "db-replica replication lag")
        assert result.startswith("[LOW CONFIDENCE: 54%]")

    def test_no_prefix_at_threshold(self) -> None:
        result = label_if_low(MIN_CONFIDENCE, "some text")
        assert not result.startswith("[LOW CONFIDENCE")

    def test_no_prefix_above_threshold(self) -> None:
        result = label_if_low(0.89, "payment gateway exhausted")
        assert result == "payment gateway exhausted"

    def test_prefix_format_is_canonical(self) -> None:
        result = label_if_low(0.30, "uncertain")
        assert result == "[LOW CONFIDENCE: 30%] uncertain"
