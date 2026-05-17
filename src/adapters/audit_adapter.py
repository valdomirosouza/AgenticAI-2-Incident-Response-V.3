"""Audit adapter — GCS WORM append-only audit trail (spec 17, ADR-0024, ADR-0025)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone

from src.domain.exceptions import AuditWriteFailure
from src.domain.models.audit import AuditEvent, ChainValidationResult
from src.ports.audit_port import AuditPort

logger = logging.getLogger(__name__)

_GENESIS_HASH = "sha256:" + "0" * 64


class GCSAuditAdapter(AuditPort):
    """Writes audit events to GCS WORM bucket with SHA-256 hash-chain integrity."""

    def __init__(self) -> None:
        self._bucket = os.environ.get("AUDIT_GCS_BUCKET", "audit-trail")

    async def append(self, event: AuditEvent) -> None:
        try:
            from google.cloud import storage  # type: ignore[import]

            client = storage.Client()
            bucket = client.bucket(self._bucket)
            blob_name = f"{event.incident_id}/{event.record_id}.json"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(
                event.model_dump_json(),
                content_type="application/json",
            )
        except Exception as exc:
            logger.critical(
                "audit_write_failure",
                extra={"record_id": event.record_id, "error": str(exc)},
            )
            raise AuditWriteFailure(
                f"Audit write failed for {event.record_id}: {exc}"
            ) from exc

    async def validate_chain(self, incident_id: str) -> ChainValidationResult:
        events = await self.get_events(incident_id)
        prev = _GENESIS_HASH
        for event in events:
            if event.prev_hash != prev:
                return ChainValidationResult(
                    incident_id=incident_id,
                    valid=False,
                    record_count=len(events),
                    first_broken_link=event.record_id,
                    validated_at=datetime.now(tz=timezone.utc),
                )
            prev = event.record_hash
        return ChainValidationResult(
            incident_id=incident_id,
            valid=True,
            record_count=len(events),
            first_broken_link=None,
            validated_at=datetime.now(tz=timezone.utc),
        )

    async def get_events(self, incident_id: str) -> list[AuditEvent]:
        try:
            from google.cloud import storage  # type: ignore[import]

            client = storage.Client()
            bucket = client.bucket(self._bucket)
            blobs = sorted(
                bucket.list_blobs(prefix=f"{incident_id}/"),
                key=lambda b: b.name,
            )
            return [AuditEvent.model_validate_json(b.download_as_text()) for b in blobs]
        except Exception as exc:
            logger.error("audit_get_events_failed", extra={"incident_id": incident_id, "error": str(exc)})
            return []
