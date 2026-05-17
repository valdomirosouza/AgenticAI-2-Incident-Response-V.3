"""Security: BLOCKED action enforcement — all three types refused at every layer (spec 16 §3.5).

This test file validates defence-in-depth across the ActionExecutor, RemediationAgent, and
the ActionType model itself. A BLOCKED action must be refused regardless of token presence.
"""

import pytest

from src.adapters.action_executor import ActionExecutor
from src.agents.remediation_agent import RemediationAgent
from src.domain.exceptions import BlockedActionError
from src.domain.models.remediation import ActionType, BLOCKED_ACTION_TYPES


@pytest.mark.security
class TestBlockedAtActionExecutor:
    """Layer 5 — ActionExecutor._dispatch table never receives BLOCKED types."""

    @pytest.fixture
    def executor(self, mock_hitl_port):
        return ActionExecutor(hitl_port=mock_hitl_port)

    @pytest.mark.asyncio
    async def test_data_delete_blocked_without_token(
        self, executor, proposal_data_delete
    ) -> None:
        with pytest.raises(BlockedActionError) as exc_info:
            await executor.execute(proposal_data_delete, token=None)
        assert "BLOCKED" in str(exc_info.value)
        assert "data_delete" in str(exc_info.value).lower() or "PRODUCTION_data_delete" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_data_delete_blocked_even_with_token(
        self, executor, proposal_data_delete, valid_approval_token
    ) -> None:
        """BLOCKED actions must be refused even if a token is supplied — no approval path."""
        with pytest.raises(BlockedActionError):
            await executor.execute(proposal_data_delete, token=valid_approval_token)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("blocked_type", list(BLOCKED_ACTION_TYPES))
    async def test_all_blocked_types_refused(
        self, executor, mock_hitl_port, blocked_type: ActionType
    ) -> None:
        from src.domain.models.remediation import RemediationProposal

        proposal = RemediationProposal(
            incident_id="INC-TEST-SEC",
            action_type=blocked_type,
            target_service="test-service",
            rationale="security test",
            predicted_effect="none",
            confidence=0.9,
            risk_estimate="high",
        )
        with pytest.raises(BlockedActionError):
            await executor.execute(proposal, token=None)


@pytest.mark.security
class TestBlockedAtRemediationAgent:
    """Layer 1 — RemediationAgent._guard_blocked refuses before reaching executor."""

    @pytest.fixture
    def agent(self, mock_audit_port, mock_llm_port, mock_hitl_port):
        return RemediationAgent(
            audit_port=mock_audit_port,
            llm_port=mock_llm_port,
            hitl_port=mock_hitl_port,
        )

    @pytest.mark.parametrize("blocked_type", [
        ActionType.PRODUCTION_DATA_DELETE,
        ActionType.PRODUCTION_IAM_CHANGE,
        ActionType.PRODUCTION_FIREWALL_CHANGE,
    ])
    def test_guard_blocked_raises_for_all_types(
        self, agent, blocked_type: ActionType
    ) -> None:
        with pytest.raises(BlockedActionError):
            agent._guard_blocked(blocked_type.value)

    def test_guard_blocked_passes_for_hitl_type(self, agent) -> None:
        agent._guard_blocked(ActionType.PRODUCTION_POD_RESTART.value)  # must not raise


@pytest.mark.security
class TestBlockedActionTypeModel:
    """Validate that blocked set and hitl set are disjoint at model level."""

    def test_no_overlap_between_blocked_and_hitl(self) -> None:
        from src.domain.models.remediation import HITL_ACTION_TYPES
        assert BLOCKED_ACTION_TYPES.isdisjoint(HITL_ACTION_TYPES)

    def test_blocked_set_immutable(self) -> None:
        with pytest.raises((AttributeError, TypeError)):
            BLOCKED_ACTION_TYPES.add(ActionType.PRODUCTION_POD_RESTART)  # type: ignore[attr-defined]
