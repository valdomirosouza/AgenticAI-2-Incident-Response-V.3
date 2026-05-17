"""PII sanitizer guardrail — ADR-0028, spec 19, OWASP LLM Top 10 LLM02."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Minimum Presidio confidence score to treat an entity as PII — spec 19 §3.2
PRESIDIO_SCORE_THRESHOLD: float = 0.7

# Redaction placeholder — must not carry any original PII character pattern
_REDACTED = "[REDACTED]"

# Fallback regex patterns applied when Presidio is unavailable — defence-in-depth
_FALLBACK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("BR_CPF", re.compile(r"\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-]?\d{2}\b")),
    ("BR_CNPJ", re.compile(r"\b\d{2}[.\-]?\d{3}[.\-]?\d{3}[/\-]?\d{4}[.\-]?\d{2}\b")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("PHONE_BR", re.compile(r"\b(?:\+55\s?)?(?:\(\d{2}\)\s?)?\d{4,5}[.\-\s]?\d{4}\b")),
    ("IPV4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def sanitize(text: str, *, incident_id: str = "SYSTEM") -> str:
    """Return text with all detected PII replaced by [REDACTED].

    Attempts Presidio AnalyzerEngine first; falls back to regex patterns.
    Input is truncated to 2000 characters before LLM submission — spec 19 §3.3.
    """
    if not text:
        return text

    sanitized = _try_presidio(text, incident_id=incident_id)
    if sanitized is None:
        sanitized = _fallback_regex(text)
        logger.warning(
            "pii_sanitizer_presidio_unavailable_fallback_used",
            extra={"incident_id": incident_id},
        )

    redacted_count = sanitized.count(_REDACTED)
    if redacted_count:
        logger.info(
            "pii_masked",
            extra={"incident_id": incident_id, "redacted_count": redacted_count},
        )

    return sanitized


def truncate_for_llm(text: str) -> str:
    """Truncate text to 2000 characters — max safe window before LLM call (spec 19 §3.3)."""
    return text[:2000]


def _try_presidio(text: str, *, incident_id: str) -> str | None:
    """Return Presidio-sanitized text, or None when Presidio is not installed."""
    try:
        from presidio_analyzer import AnalyzerEngine  # type: ignore[import]
        from presidio_anonymizer import AnonymizerEngine  # type: ignore[import]
        from presidio_anonymizer.entities import OperatorConfig  # type: ignore[import]

        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        results = analyzer.analyze(text=text, language="en", score_threshold=PRESIDIO_SCORE_THRESHOLD)
        # Also run Portuguese entity detection for BR_CPF / BR_CNPJ
        results += analyzer.analyze(text=text, language="pt", score_threshold=PRESIDIO_SCORE_THRESHOLD)

        if not results:
            return text

        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": OperatorConfig("replace", {"new_value": _REDACTED})},
        )
        return anonymized.text

    except ImportError:
        return None


def _fallback_regex(text: str) -> str:
    result = text
    for _label, pattern in _FALLBACK_PATTERNS:
        result = pattern.sub(_REDACTED, result)
    return result
