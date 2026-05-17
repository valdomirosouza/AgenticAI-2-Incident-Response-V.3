"""Kill-switch guardrail — ADR-0025, spec 16 §3.6, EU AI Act Art. 14."""

from __future__ import annotations

import logging
import threading

from src.domain.exceptions import KillSwitchActivated

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_active: bool = False
_activated_by: str = "system"
_reason: str = ""


def activate(*, activated_by: str, reason: str) -> None:
    """Engage kill-switch — all PRODUCTION_* actions are refused after this call.

    Must be recorded as AGENT_KILL_SWITCH_ACTIVATED audit event before returning.
    RTO target: <60 seconds from trigger to full enforcement — ADR-0025.
    """
    global _active, _activated_by, _reason
    with _lock:
        _active = True
        _activated_by = activated_by
        _reason = reason
    logger.critical(
        "kill_switch_activated",
        extra={"activated_by": activated_by, "reason": reason},
    )


def deactivate(*, deactivated_by: str) -> None:
    """Disengage kill-switch — requires explicit operator action, never automatic."""
    global _active
    with _lock:
        _active = False
    logger.warning(
        "kill_switch_deactivated",
        extra={"deactivated_by": deactivated_by},
    )


def is_active() -> bool:
    """Return True when kill-switch is currently engaged."""
    with _lock:
        return _active


def enforce() -> None:
    """Raise KillSwitchActivated when switch is active.

    Call this at the top of every PRODUCTION_* action path.
    """
    with _lock:
        active = _active
        reason = _reason
        activated_by = _activated_by
    if active:
        raise KillSwitchActivated(
            f"Kill-switch is active (activated_by={activated_by}): {reason}"
        )
