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

References: Spec LIM-01 §3.7, §3.8, ADR-0028 (client_ip boundary).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import ValidationError

from log_ingestion.api.dependencies import get_ingestion_service
from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry
from log_ingestion.observability import metrics as obs
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
            entry = HaproxyLogEntry.model_validate(raw)
            accepted.append(entry)
        except ValidationError as exc:
            rejected += 1
            if len(errors) < _MAX_ERRORS:
                first_msg = exc.errors()[0]["msg"]
                errors.append(f"entry {i}: {first_msg}")

    obs.record_ingestion_batch(len(raw_entries))

    # Emit per-entry accepted / parse_error counters grouped by backend where known.
    # Rejected entries have no parsed backend; use "_unknown" as the label value.
    if accepted:
        # Group by backend to minimise instrument.add() calls
        from collections import defaultdict  # noqa: PLC0415

        backend_counts: dict[str, int] = defaultdict(int)
        for entry in accepted:
            backend_counts[entry.backend] += 1
        for backend, count in backend_counts.items():
            obs.record_ingestion_event(backend, "accepted", count)

    if rejected:
        obs.record_ingestion_event("_unknown", "parse_error", rejected)

    await ingestion_svc.ingest(accepted)

    return {"accepted": len(accepted), "rejected": rejected, "errors": errors}
