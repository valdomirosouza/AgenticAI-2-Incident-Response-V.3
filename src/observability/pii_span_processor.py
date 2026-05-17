"""PII span processor — scrubs PII from OTel span attributes before export (ADR-0028)."""

from __future__ import annotations

import logging

from src.guardrails import pii_sanitizer

logger = logging.getLogger(__name__)

_SENSITIVE_ATTRS = frozenset({
    "log.message",
    "exception.message",
    "exception.stacktrace",
    "db.statement",
    "http.request.body",
    "http.response.body",
})


class PiiSpanProcessor:
    """OpenTelemetry SpanProcessor that redacts PII from span attributes on end."""

    def on_start(self, span, parent_context=None) -> None:
        pass

    def on_end(self, span) -> None:
        try:
            for key in list(span.attributes or {}):
                if key in _SENSITIVE_ATTRS:
                    original = str(span.attributes[key])
                    scrubbed = pii_sanitizer.sanitize(original)
                    if scrubbed != original:
                        span.set_attribute(key, scrubbed)
        except Exception as exc:
            logger.error("pii_span_processor_error", extra={"error": str(exc)})

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
