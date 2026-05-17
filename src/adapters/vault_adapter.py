"""Vault adapter — HashiCorp Vault secrets (ADR-0023, RULE-C03)."""

from __future__ import annotations

import logging
import os

from src.ports.secrets_port import SecretsPort

logger = logging.getLogger(__name__)


class VaultAdapter(SecretsPort):
    """Reads secrets from HashiCorp Vault; never reads from env vars directly."""

    def __init__(self) -> None:
        self._addr = os.environ.get("VAULT_ADDR", "http://vault:8200")
        # Token for Vault auth is read from env — injected by K8s secret (RULE-C03)
        self._token_env = "VAULT_TOKEN"

    async def get_secret(self, path: str) -> str:
        import httpx

        headers = {"X-Vault-Token": os.environ[self._token_env]}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._addr}/v1/{path}",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()["data"]["value"]

    async def get_hmac_key(self, key_id: str) -> bytes:
        raw = await self.get_secret(key_id)
        return bytes.fromhex(raw)
