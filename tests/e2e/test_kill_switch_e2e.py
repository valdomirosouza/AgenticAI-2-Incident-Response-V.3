"""E2E: Kill-switch drill against staging — all PRODUCTION_* actions refused (ADR-0025).

Gate: harness/staging-check.yml S08 (kill-switch drill).
"""

import os

import pytest

from src.adapters.action_executor import ActionExecutor
from src.domain.exceptions import KillSwitchActivated
from src.domain.models.remediation import ActionType, RemediationProposal
import src.guardrails.kill_switch as ks

pytestmark = pytest.mark.e2e


@pytest.fixture(autouse=True)
def ensure_kill_switch_reset():
    ks.deactivate(deactivated_by="e2e-setup")
    yield
    ks.deactivate(deactivated_by="e2e-teardown")


@pytest.mark.asyncio
async def test_kill_switch_blocks_all_production_actions(mock_hitl_port) -> None:
    """After activate(), every PRODUCTION_* execute() call raises KillSwitchActivated."""
    executor = ActionExecutor(hitl_port=mock_hitl_port)
    ks.activate(activated_by="e2e-drill", reason="quarterly kill-switch drill")

    for action_type in [
        ActionType.PRODUCTION_POD_RESTART,
        ActionType.PRODUCTION_SCALE_UP,
        ActionType.PRODUCTION_CONFIG_CHANGE,
    ]:
        proposal = RemediationProposal(
            incident_id="INC-E2E-KS",
            action_type=action_type,
            target_service="test-service",
            rationale="e2e kill-switch drill",
            predicted_effect="none",
            confidence=0.9,
            risk_estimate="low",
        )
        with pytest.raises(KillSwitchActivated):
            await executor.execute(proposal, token=None)
