"""Secrets outbound port — ADR-0002, ADR-0023 (Vault S-02 key)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecretsPort(ABC):
    """Contract for reading secrets from Vault — never from env vars directly."""

    @abstractmethod
    async def get_secret(self, path: str) -> str:
        """Return secret value at Vault path."""

    @abstractmethod
    async def get_hmac_key(self, key_id: str) -> bytes:
        """Return HMAC signing key bytes for token validation — ADR-0023."""
