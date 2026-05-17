"""ActionExecutor — HITL-enforced PRODUCTION_* action runner (spec 16, ADR-0023)."""

from __future__ import annotations

import logging

from src.domain.exceptions import (
    BlockedActionError,
    HITLTokenRequired,
    KillSwitchActivated,
)
from src.domain.models.remediation import (
    BLOCKED_ACTION_TYPES,
    HITL_ACTION_TYPES,
    ActionType,
    ApprovalToken,
    RemediationProposal,
)
from src.guardrails import kill_switch
from src.ports.hitl_port import HITLPort

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Single entry point for all PRODUCTION_* action execution.

    Enforcement layers (defence-in-depth — spec 16 §3.5):
      1. Kill-switch check (kill_switch.enforce)
      2. BLOCKED actions → BlockedActionError (no approval path exists)
      3. HITL actions → ApprovalToken required → HITLTokenRequired if absent
      4. HITL token validation → HITLPort.validate_token()
      5. Execution of the action
    """

    def __init__(self, hitl_port: HITLPort) -> None:
        self._hitl = hitl_port

    async def execute(
        self,
        proposal: RemediationProposal,
        token: ApprovalToken | None = None,
    ) -> dict:
        """Execute remediation proposal after all governance checks pass."""
        # Layer 1: kill-switch
        kill_switch.enforce()

        action_type = proposal.action_type

        # Layer 2: BLOCKED actions — no approval path exists
        if action_type in BLOCKED_ACTION_TYPES:
            raise BlockedActionError(
                f"Action {action_type.value} is BLOCKED — "
                "no approval path exists (spec 16 §3.5, ADR-0023)"
            )

        # Layer 3: HITL actions require a valid ApprovalToken
        if action_type in HITL_ACTION_TYPES:
            if token is None:
                raise HITLTokenRequired(
                    f"Action {action_type.value} requires an ApprovalToken — ADR-0023"
                )
            # Layer 4: validate token signature and expiry
            await self._hitl.validate_token(
                token,
                incident_id=proposal.incident_id,
                action_type=action_type.value,
            )

        # Layer 5: dispatch to platform-specific execution handler
        logger.info(
            "action_executing",
            extra={
                "incident_id": proposal.incident_id,
                "action_type": action_type.value,
                "target_service": proposal.target_service,
            },
        )
        return await self._dispatch(proposal)

    async def _dispatch(self, proposal: RemediationProposal) -> dict:
        """Route to the correct platform handler by action_type."""
        handler = _DISPATCH_TABLE.get(proposal.action_type)
        if handler is None:
            return {"status": "no_op", "action_type": proposal.action_type.value}
        return await handler(proposal)


async def _pod_restart(proposal: RemediationProposal) -> dict:
    logger.info("executing_pod_restart", extra={"service": proposal.target_service})
    return {"status": "ok", "action": "pod_restart", "service": proposal.target_service}


async def _config_change(proposal: RemediationProposal) -> dict:
    logger.info("executing_config_change", extra={"service": proposal.target_service})
    return {"status": "ok", "action": "config_change", "service": proposal.target_service}


async def _scale_up(proposal: RemediationProposal) -> dict:
    logger.info("executing_scale_up", extra={"service": proposal.target_service})
    return {"status": "ok", "action": "scale_up", "service": proposal.target_service}


async def _scale_down(proposal: RemediationProposal) -> dict:
    logger.info("executing_scale_down", extra={"service": proposal.target_service})
    return {"status": "ok", "action": "scale_down", "service": proposal.target_service}


async def _traffic_shift(proposal: RemediationProposal) -> dict:
    logger.info("executing_traffic_shift", extra={"service": proposal.target_service})
    return {"status": "ok", "action": "traffic_shift", "service": proposal.target_service}


async def _db_query(proposal: RemediationProposal) -> dict:
    logger.info("executing_db_query", extra={"service": proposal.target_service})
    return {"status": "ok", "action": "db_query", "service": proposal.target_service}


async def _secret_rotation(proposal: RemediationProposal) -> dict:
    logger.info("executing_secret_rotation", extra={"service": proposal.target_service})
    return {"status": "ok", "action": "secret_rotation", "service": proposal.target_service}


_DISPATCH_TABLE: dict = {
    ActionType.PRODUCTION_POD_RESTART: _pod_restart,
    ActionType.PRODUCTION_CONFIG_CHANGE: _config_change,
    ActionType.PRODUCTION_SCALE_UP: _scale_up,
    ActionType.PRODUCTION_SCALE_DOWN: _scale_down,
    ActionType.PRODUCTION_TRAFFIC_SHIFT: _traffic_shift,
    ActionType.PRODUCTION_DB_QUERY: _db_query,
    ActionType.PRODUCTION_SECRET_ROTATION: _secret_rotation,
}
