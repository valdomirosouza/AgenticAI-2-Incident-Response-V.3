"""RCA hypothesis domain model — spec 02, spec 03, ADR-0021."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RCAHypothesis(BaseModel):
    """Root cause hypothesis produced by RCAAgent."""

    incident_id: str
    root_cause: str = Field(description="Human-readable root cause description")
    contributing_factors: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(
        default_factory=list,
        description="Log/trace excerpts supporting the hypothesis (sanitized)",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score — values < 0.6 trigger LOW_CONFIDENCE label (ADR-0021)",
    )
    explanation: str = Field(
        description="XAI explanation — why this root cause was inferred (EU AI Act Art. 13)"
    )
