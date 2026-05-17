"""Domain models for Golden Signal MetricPoints and analytics query results.

Supports RQ1 (MTTD reduction): MetricPoint is the unit of measurement produced by the
log parser and consumed by the metric store port. AnalyticsResult is the response payload
returned by GET /analytics to the DetectionAgent.

References: Spec LIM-01 §3.4 (Golden Signal extraction); Spec LIM-02 §3.2 (response schema);
ADR-0011 (Golden Signals), ADR-0035 (exact percentile algorithm).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class SignalType(StrEnum):
    """Four Golden Signals tracked per backend+path+window bucket (ADR-0011)."""

    TRAFFIC = "traffic"
    ERROR = "error"
    LATENCY = "latency"
    SATURATION = "saturation"


class MetricPoint(BaseModel):
    """Immutable value object: one Golden Signal measurement for a backend+path+window."""

    model_config = ConfigDict(frozen=True)

    signal: SignalType
    value: float
    backend: str
    path: str
    window_ts: int  # Unix epoch floor of the window bucket (Spec LIM-01 §3.5)


class TrafficMetric(BaseModel):
    total_requests: int
    rps: float


class ErrorMetric(BaseModel):
    rate_4xx: float
    rate_5xx: float
    total_4xx: int
    total_5xx: int


class SaturationMetric(BaseModel):
    high_wait_pct: float
    threshold_wait_ms: int


class AnalyticsResult(BaseModel):
    """Response payload for GET /analytics (Spec LIM-02 §3.2).

    Optional signal fields are absent (not null) when filtered via the `signal` query
    parameter. Routers must call `model_dump(exclude_none=True)` when serialising.
    `path == "*"` indicates multi-path aggregation is active (Spec LIM-02 §3.5).
    """

    backend: str
    path: str
    window: str
    window_start_iso: str
    traffic: TrafficMetric | None = None
    errors: ErrorMetric | None = None
    latency_ms: dict[str, float] | None = None  # e.g. {"p50": 32.0, "p95": 145.0, "p99": 412.0}
    saturation: SaturationMetric | None = None
