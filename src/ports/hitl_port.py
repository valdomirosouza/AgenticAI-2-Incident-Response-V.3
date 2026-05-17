"""HITL outbound port — spec 16, ADR-0002, ADR-0023."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.models.remediation import ApprovalToken, RemediationProposal


class HITLPort(ABC):
    """Contract for requesting and validating human-in-the-loop approvals."""

    @abstractmethod
    async def request_approval(
        self,
        proposal: RemediationProposal,
        *,
        trace_id: str,
    ) -> UUID:
        """Dispatch approval request to on-call engineer; return request token_id."""

    @abstractmethod
    async def get_token(self, token_id: UUID) -> ApprovalToken | None:
        """Return ApprovalToken if approved, None if pending."""

    @abstractmethod
    async def validate_token(
        self,
        token: ApprovalToken,
        *,
        incident_id: str,
        action_type: str,
    ) -> None:
        """Verify HMAC signature and expiry.

        Raises HITLTokenExpired when token.expires_at is in the past.
        Raises HITLTokenInvalid when HMAC verification fails.
        """
