"""Integration tests for HITLAdapter token validation — requires Vault (ADR-0023).

Skipped unless VAULT_ADDR and VAULT_TOKEN are set in the environment.
Gate: harness/staging-check.yml S03 (HITL e2e).
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.adapters.hitl_adapter import HITLAdapter
from src.adapters.vault_adapter import VaultAdapter
from src.domain.exceptions import HITLTokenExpired, HITLTokenInvalid
from src.domain.models.remediation import ActionType, ApprovalToken


pytestmark = pytest.mark.integration


@pytest.fixture
def hitl_adapter() -> HITLAdapter:
    if not (os.environ.get("VAULT_ADDR") and os.environ.get("VAULT_TOKEN")):
        pytest.skip("Vault credentials not set — integration test skipped")
    return HITLAdapter(secrets_port=VaultAdapter())


@pytest.mark.asyncio
async def test_expired_token_raises(hitl_adapter: HITLAdapter) -> None:
    past = datetime.now(tz=timezone.utc) - timedelta(hours=2)
    token = ApprovalToken(
        token_id=uuid4(),
        incident_id="INC-INTEG-001",
        action_type=ActionType.PRODUCTION_POD_RESTART,
        approver_role="sre-lead",
        approved_at=past - timedelta(minutes=15),
        expires_at=past,
        signature="any",
    )
    with pytest.raises(HITLTokenExpired):
        await hitl_adapter.validate_token(
            token,
            incident_id="INC-INTEG-001",
            action_type=ActionType.PRODUCTION_POD_RESTART.value,
        )
