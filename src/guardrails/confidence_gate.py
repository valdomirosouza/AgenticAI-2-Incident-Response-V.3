"""Confidence gate guardrail — ADR-0021 LLM09, spec 03, spec 10."""

from __future__ import annotations

import logging

from src.domain.exceptions import ConfidenceBelowThreshold

logger = logging.getLogger(__name__)

MIN_CONFIDENCE: float = 0.6


def enforce(confidence: float, *, context: str, incident_id: str) -> None:
    """Raise ConfidenceBelowThreshold when confidence < MIN_CONFIDENCE.

    When below threshold the caller must escalate to human — no auto-execute path.
    """
    if confidence < MIN_CONFIDENCE:
        logger.warning(
            "confidence_below_threshold",
            extra={
                "incident_id": incident_id,
                "confidence": confidence,
                "threshold": MIN_CONFIDENCE,
                "context": context,
            },
        )
        raise ConfidenceBelowThreshold(
            f"[LOW CONFIDENCE: {confidence:.0%}] {context} — "
            f"threshold is {MIN_CONFIDENCE:.0%}; human escalation required"
        )


def label_if_low(value: float, text: str) -> str:
    """Prepend [LOW CONFIDENCE: XX%] prefix when value < MIN_CONFIDENCE — ADR-0021 LLM09."""
    if value < MIN_CONFIDENCE:
        return f"[LOW CONFIDENCE: {value:.0%}] {text}"
    return text
