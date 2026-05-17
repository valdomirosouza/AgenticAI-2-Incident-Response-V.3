"""Domain exceptions — enforce architectural constraints at the domain layer."""

from __future__ import annotations


class BlockedActionError(ValueError):
    """Raised when an agent attempts a BLOCKED action type — spec 16 §3.5, ADR-0023."""


class LLMOutputInvalid(ValueError):
    """Raised when LLM response fails Pydantic schema validation — ADR-0021 LLM02."""


class PiiSanitizationRequired(ValueError):
    """Raised when LLMAdapter.complete() is called without sanitized=True — ADR-0028."""


class HITLTokenRequired(ValueError):
    """Raised when action_executor.execute() is called without an ApprovalToken — ADR-0023."""


class HITLTokenExpired(ValueError):
    """Raised when ApprovalToken has passed its expires_at timestamp — ADR-0023."""


class HITLTokenInvalid(ValueError):
    """Raised when ApprovalToken HMAC signature verification fails — ADR-0023."""


class UnknownMessageTypeError(ValueError):
    """Raised when an AgentMessage has an unrecognised MessageType — spec 02 §3.4."""


class AuditWriteFailure(RuntimeError):
    """Raised when the audit trail write fails — triggers kill-switch (ADR-0024, ADR-0025)."""


class KillSwitchActivated(RuntimeError):
    """Raised when the kill-switch is active — all PRODUCTION_* actions are refused."""


class ConfidenceBelowThreshold(ValueError):
    """Raised when confidence < MIN_CONFIDENCE and escalation is required — ADR-0021 LLM09."""
