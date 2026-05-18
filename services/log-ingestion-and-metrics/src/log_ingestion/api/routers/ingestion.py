"""POST /ingestion router — HAProxy log ingestion with partial-failure semantics.

Accepts a single HAProxy log entry (JSON object) or a batch (JSON array, max 1 000).
Each entry is validated individually so that valid siblings are processed even when
some entries are malformed (Spec LIM-01 §3.7).

Batch size limit:
  Arrays longer than 1 000 entries receive 422 before any validation or storage.

Partial-failure response (always 202):
  {
    "accepted": <int>,   # entries that passed validation and were stored
    "rejected": <int>,   # entries that failed Pydantic validation
    "errors":   [<str>]  # up to 10 error strings (one per rejected entry)
  }

References: Spec LIM-01 §3.7, ADR-0028 (client_ip boundary).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import ValidationError

from log_ingestion.api.dependencies import get_ingestion_service
from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry
from log_ingestion.ports.ingestion_port import IngestionPort

router = APIRouter(tags=["ingestion"])

_MAX_BATCH: int = 1_000
_MAX_ERRORS: int = 10


@router.post("/ingestion", status_code=202)
async def ingest(
    body: Annotated[list[Any] | dict[str, Any], Body()],
    ingestion_svc: Annotated[IngestionPort, Depends(get_ingestion_service)],
) -> dict[str, Any]:
    """Ingest a single entry (object) or batch (array) of HAProxy JSON log entries."""
    raw_entries: list[Any] = [body] if isinstance(body, dict) else body

    if len(raw_entries) > _MAX_BATCH:
        raise HTTPException(
            status_code=422,
            detail=f"Batch exceeds {_MAX_BATCH} entries — received {len(raw_entries)}.",
        )

    accepted: list[HaproxyLogEntry] = []
    rejected: int = 0
    errors: list[str] = []

    for i, raw in enumerate(raw_entries):
        try:
            accepted.append(HaproxyLogEntry.model_validate(raw))
        except ValidationError as exc:
            rejected += 1
            if len(errors) < _MAX_ERRORS:
                first_msg = exc.errors()[0]["msg"]
                errors.append(f"entry {i}: {first_msg}")

    await ingestion_svc.ingest(accepted)

    return {"accepted": len(accepted), "rejected": rejected, "errors": errors}
