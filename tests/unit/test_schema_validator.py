"""Unit tests for src/guardrails/schema_validator.py — ADR-0021 LLM02."""

import json

import pytest
from pydantic import BaseModel

from src.domain.exceptions import LLMOutputInvalid
from src.guardrails.schema_validator import parse_llm_output


class _SimpleSchema(BaseModel):
    name: str
    value: int


@pytest.mark.unit
class TestParseOutput:
    def test_valid_json_and_schema_returns_model(self) -> None:
        raw = json.dumps({"name": "payment-service", "value": 42})
        result = parse_llm_output(raw, _SimpleSchema, context="test")
        assert result.name == "payment-service"
        assert result.value == 42

    def test_invalid_json_raises_llm_output_invalid(self) -> None:
        with pytest.raises(LLMOutputInvalid) as exc_info:
            parse_llm_output("not json {{{", _SimpleSchema, context="rca_parse")
        assert "rca_parse" in str(exc_info.value)
        assert "not valid JSON" in str(exc_info.value)

    def test_valid_json_wrong_schema_raises(self) -> None:
        raw = json.dumps({"name": "ok", "value": "not-an-int"})
        with pytest.raises(LLMOutputInvalid) as exc_info:
            parse_llm_output(raw, _SimpleSchema, context="schema_mismatch")
        assert "schema_mismatch" in str(exc_info.value)

    def test_missing_required_field_raises(self) -> None:
        raw = json.dumps({"name": "only-name"})
        with pytest.raises(LLMOutputInvalid):
            parse_llm_output(raw, _SimpleSchema, context="missing_field")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(LLMOutputInvalid):
            parse_llm_output("", _SimpleSchema, context="empty")
