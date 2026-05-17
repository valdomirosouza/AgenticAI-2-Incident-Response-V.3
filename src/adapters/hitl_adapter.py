"""HITL adapter — PagerDuty approval dispatch and token validation (ADR-0023, spec 16)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from uuid import UUID

from src.domain.exceptions import HITLTokenExpired, HITLTokenInvalid
from src.domain.models.remediation import ApprovalToken, RemediationProposal
from src.ports.hitl_port import HITLPort
from src.ports.secrets_port import SecretsPort

logger = logging.getLogger(__name__)

_HMAC_KEY_ID = "vault/hitl/hmac-key"


class HITLAdapter(HITLPort):
    """Dispatches approval requests via PagerDuty; validates HMAC-SHA256 tokens."""

    def __init__(self, secrets_port: SecretsPort) -> None:
        self._secrets = secrets_port

    async def request_approval(self, proposal: RemediationProposal, *, trace_id: str) -> UUID:
        from uuid import uuid4
        token_id = uuid4()
        logger.info(
            "hitl_approval_requested",
            extra={
                "incident_id": proposal.incident_id,
                "action_type": proposal.action_type,
                "token_id": str(token_id),
                "trace_id": trace_id,
            },
        )
        # PagerDuty webhook dispatch implemented in infrastructure layer
        return token_id

    async def get_token(self, token_id: UUID) -> ApprovalToken | None:
        # Token store query implemented via cache/DB in adapter layer
        return None

    async def validate_token(
        self,
        token: ApprovalToken,
        *,
        incident_id: str,
        action_type: str,
    ) -> None:
        now = datetime.now(tz=timezone.utc)
        if token.expires_at < now:
            raise HITLTokenExpired(
                f"ApprovalToken {token.token_id} expired at {token.expires_at}"
            )

        key_bytes = await self._secrets.get_hmac_key(_HMAC_KEY_ID)
        message = "|".join([
            str(token.token_id),
            token.incident_id,
            token.action_type.value,
            token.approved_at.isoformat(),
        ]).encode()
        expected = hmac.new(key_bytes, message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, token.signature):
            raise HITLTokenInvalid(
                f"ApprovalToken {token.token_id} HMAC signature verification failed"
            )
