"""Domain models for HAProxy JSON log entries.

Supports RQ1 (MTTD reduction): validates the ingestion schema and enforces the batch
size contract so the downstream log parser receives only well-formed, bounded input.

References: Spec LIM-01 §3.1 (schema), §3.3 (PII), §3.7 (batch limit); ADR-0028.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel


class HaproxyTimers(BaseModel):
    """HAProxy per-request timing breakdown, all values in milliseconds."""

    model_config = ConfigDict(frozen=True)

    total_time: Annotated[int, Field(ge=0)]
    wait: Annotated[int, Field(ge=0)]
    connect: Annotated[int, Field(ge=0)]
    response: Annotated[int, Field(ge=0)]


class HaproxyLogEntry(BaseModel):
    """Single HAProxy JSON log entry as emitted by the ingress layer.

    `client_ip` is PII under LGPD art. 5 I and GDPR art. 4(1). It is accepted here
    for schema validation only. Callers must never write it to Redis, structured logs,
    OTel span attributes, or any other persistent store (Spec LIM-01 §3.3, ADR-0028).
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    client_ip: str
    client_port: Annotated[int, Field(ge=0, le=65535)]
    frontend: str
    backend: str
    server: str
    status_code: Annotated[int, Field(ge=0, le=599)]
    bytes_read: Annotated[int, Field(ge=0)]
    request: str
    termination_state: str
    timers: HaproxyTimers


class HaproxyLogBatch(RootModel[Annotated[list[HaproxyLogEntry], Field(max_length=1000)]]):
    """Batch of HAProxy log entries, maximum 1 000 per call (Spec LIM-01 §3.7).

    Batches exceeding 1 000 entries are rejected with 422 before any processing occurs.
    """
