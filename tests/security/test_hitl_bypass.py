"""Security: HITL bypass prevention — PRODUCTION_* actions require ApprovalToken (ADR-0023).

OWASP LLM Top 10: LLM08 — Excessive Agency.
Validates that the ActionExecutor never executes PRODUCTION_* actions without a token.
"""

import pytest

from src.adapters.action_executor import ActionExecutor
from src.domain.exceptions import HITLTokenRequired, KillSwitchActivated
from src.domain.models.remediation import ActionType, HITL_ACTION_TYPES, RemediationProposal


def _make_proposal(action_type: ActionType) -> RemediationProposal:
    return RemediationProposal(
        incident_id="INC-SEC-HITL",
        action_type=action_type,
        target_service="test-service",
        rationale="security test",
        predicted_effect="none",
        confidence=0.9,
        risk_estimate="medium",
    )


@pytest.mark.security
class TestHITLBypassPrevention:
    @pytest.fixture
    def executor(self, mock_hitl_port):
        return ActionExecutor(hitl_port=mock_hitl_port)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("action_type", list(HITL_ACTION_TYPES))
    async def test_hitl_action_without_token_raises(
        self, executor, action_type: ActionType
    ) -> None:
        """Every HITL action type must raise HITLTokenRequired when token=None."""
        with pytest.raises(HITLTokenRequired) as exc_info:
            await executor.execute(_make_proposal(action_type), token=None)
        assert action_type.value in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_pod_restart_with_valid_token_proceeds(
        self, executor, proposal_pod_restart, valid_approval_token, mock_hitl_port
    ) -> None:
        """With a valid token, execute() must call validate_token and dispatch."""
        result = await executor.execute(proposal_pod_restart, token=valid_approval_token)
        mock_hitl_port.validate_token.assert_awaited_once()
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_kill_switch_blocks_before_hitl_check(
        self, executor, proposal_pod_restart, valid_approval_token
    ) -> None:
        """Kill-switch (layer 1) must fire before HITL token check (layer 3)."""
        import src.guardrails.kill_switch as ks
        ks.activate(activated_by="security-test", reason="testing kill-switch priority")
        try:
            with pytest.raises(KillSwitchActivated):
                await executor.execute(proposal_pod_restart, token=valid_approval_token)
        finally:
            ks.deactivate(deactivated_by="security-test-teardown")
