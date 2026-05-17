"""Schema validator guardrail — ADR-0021 LLM02, spec 04."""

from __future__ import annotations

import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from src.domain.exceptions import LLMOutputInvalid

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def parse_llm_output(raw: str, schema: type[T], *, context: str) -> T:
    """Parse and validate LLM JSON output against a Pydantic schema.

    Raises LLMOutputInvalid when the output does not conform — ADR-0021 LLM02.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(
            "llm_output_json_parse_failed",
            extra={"context": context, "error": str(exc)},
        )
        raise LLMOutputInvalid(
            f"LLM output is not valid JSON [{context}]: {exc}"
        ) from exc

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        logger.error(
            "llm_output_schema_validation_failed",
            extra={"context": context, "errors": exc.errors()},
        )
        raise LLMOutputInvalid(
            f"LLM output failed schema validation [{context}]: {exc}"
        ) from exc
