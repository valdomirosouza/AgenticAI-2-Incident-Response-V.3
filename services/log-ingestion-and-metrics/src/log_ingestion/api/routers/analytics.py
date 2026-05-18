"""GET /analytics router — Golden Signal query with exact percentile calculation.

Reads traffic, error, latency, and saturation metrics from Redis via MetricStorePort.
Latency percentiles are computed exactly using PercentileCalculator (ADR-0035).

Multi-path aggregation (Spec LIM-02 §3.5):
  When ``path`` is omitted, SCAN discovers all per-path keys for the requested backend
  and window; counters are summed, latency sorted sets are merged via ZUNIONSTORE into a
  temporary key (deleted immediately after the query).

Signal filtering (Spec LIM-02 §3.6):
  When ``signal`` is provided only the corresponding section is populated; absent sections
  are omitted from the JSON response (not null, not 0 — entirely absent).

References: Spec LIM-02 §3.1–§3.6, ADR-0002, ADR-0034, ADR-0035.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query

from log_ingestion.api.dependencies import get_metric_store
from log_ingestion.observability import metrics as obs
from log_ingestion.domain.models.metric import (
    AnalyticsResult,
    ErrorMetric,
    SaturationMetric,
    SignalType,
    TrafficMetric,
)
from log_ingestion.domain.services.percentile_service import PercentileCalculator
from log_ingestion.ports.metric_store_port import MetricStorePort

router = APIRouter(tags=["analytics"])

_WINDOW_MAP: dict[str, int] = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}
_SAT_THRESHOLD_DEFAULT: int = 50  # matches LIM_SAT_THRESHOLD_MS default

WindowLiteral = Literal["1m", "5m", "15m", "1h"]
SignalLiteral = Literal["traffic", "error", "latency", "saturation"]


def _seg(value: str) -> str:
    return quote(value, safe="")


def _current_window_ts(window_secs: int) -> int:
    return int(time.time()) // window_secs * window_secs


@router.get("/analytics")
async def get_analytics(
    backend: Annotated[str, Query(min_length=1)],
    store: Annotated[MetricStorePort, Depends(get_metric_store)],
    path: Annotated[str | None, Query()] = None,
    signal: Annotated[SignalLiteral | None, Query()] = None,
    window: Annotated[WindowLiteral, Query()] = "5m",
    percentiles: Annotated[str, Query()] = "50,95,99",
) -> dict:
    """Return Golden Signals for a backend + optional path + time window."""
    _t0 = time.perf_counter()
    window_secs = _WINDOW_MAP[window]
    window_ts = _current_window_ts(window_secs)

    # Parse and validate percentile list
    try:
        pct_list = sorted({int(p.strip()) for p in percentiles.split(",")})
        if not pct_list or any(not 1 <= p <= 99 for p in pct_list):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="percentiles must be comma-separated integers in [1, 99]")

    b = _seg(backend)
    resolved_path: str  # "*" for multi-path, else the requested path

    if path is not None:
        # ── single-path query ──────────────────────────────────────────────────
        resolved_path = path
        p = _seg(path)

        trx_key = f"lim:trx:{b}:{p}:{window_ts}"
        traffic_count = await store.get_counter(trx_key)

        if traffic_count == 0:
            obs.record_analytics_query(signal or "all", window, "miss", time.perf_counter() - _t0)
            raise HTTPException(
                status_code=404,
                detail=f"No data for backend='{backend}' path='{path}' window='{window}'",
            )

        err4 = await store.get_counter(f"lim:err4:{b}:{p}:{window_ts}")
        err5 = await store.get_counter(f"lim:err5:{b}:{p}:{window_ts}")
        sat_count = await store.get_counter(f"lim:sat:{b}:{p}:{window_ts}")
        lat_key = f"lim:lat:{b}:{p}:{window_ts}"
        lat_card = await store.get_sorted_set_cardinality(lat_key)
        lat_keys_for_union: list[str] = [lat_key]

    else:
        # ── multi-path aggregation ─────────────────────────────────────────────
        resolved_path = "*"

        trx_keys = await store.scan_keys(f"lim:trx:{b}:*:{window_ts}")
        if not trx_keys:
            obs.record_analytics_query(signal or "all", window, "miss", time.perf_counter() - _t0)
            raise HTTPException(
                status_code=404,
                detail=f"No data for backend='{backend}' window='{window}'",
            )

        traffic_count = 0
        err4 = 0
        err5 = 0
        sat_count = 0
        lat_keys_for_union = []

        for trx_key in trx_keys:
            # Extract the path segment from the trx key to reconstruct sibling keys
            # trx key format: lim:trx:{b}:{p_encoded}:{window_ts}
            # We extract the encoded path by stripping known prefix and suffix
            prefix = f"lim:trx:{b}:"
            suffix = f":{window_ts}"
            enc_path = trx_key[len(prefix) : len(trx_key) - len(suffix)]

            traffic_count += await store.get_counter(trx_key)
            err4 += await store.get_counter(f"lim:err4:{b}:{enc_path}:{window_ts}")
            err5 += await store.get_counter(f"lim:err5:{b}:{enc_path}:{window_ts}")
            sat_count += await store.get_counter(f"lim:sat:{b}:{enc_path}:{window_ts}")
            lat_keys_for_union.append(f"lim:lat:{b}:{enc_path}:{window_ts}")

        # ZUNIONSTORE merges all per-path latency sorted sets into a temp key
        tmp_lat_key = f"lim:lat:tmp:{uuid.uuid4().hex}"
        await store.union_sorted_sets_to_temp(tmp_lat_key, lat_keys_for_union)
        lat_key = tmp_lat_key
        lat_card = await store.get_sorted_set_cardinality(lat_key)

    # ── build response sections ────────────────────────────────────────────────

    want_all = signal is None
    window_start_iso = datetime.fromtimestamp(window_ts, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    result = AnalyticsResult(
        backend=backend,
        path=resolved_path,
        window=window,
        window_start_iso=window_start_iso,
    )

    if want_all or signal == SignalType.TRAFFIC:
        rps = round(traffic_count / window_secs, 2)
        result = result.model_copy(
            update={"traffic": TrafficMetric(total_requests=traffic_count, rps=rps)}
        )

    if want_all or signal == SignalType.ERROR:
        rate_4xx = round(err4 / traffic_count, 4) if traffic_count else 0.0
        rate_5xx = round(err5 / traffic_count, 4) if traffic_count else 0.0
        result = result.model_copy(
            update={
                "errors": ErrorMetric(
                    rate_4xx=rate_4xx,
                    rate_5xx=rate_5xx,
                    total_4xx=err4,
                    total_5xx=err5,
                )
            }
        )

    if want_all or signal == SignalType.LATENCY:
        latency_ms: dict[str, float] = {}
        if lat_card > 0:
            for p_int in pct_list:
                rank = PercentileCalculator.rank_for(lat_card, p_int)
                score = await store.get_sorted_set_score_at_rank(lat_key, rank)
                latency_ms[f"p{p_int}"] = score
        result = result.model_copy(update={"latency_ms": latency_ms or None})

    if want_all or signal == SignalType.SATURATION:
        high_wait_pct = round(sat_count / traffic_count * 100, 1) if traffic_count else 0.0
        result = result.model_copy(
            update={
                "saturation": SaturationMetric(
                    high_wait_pct=high_wait_pct,
                    threshold_wait_ms=_SAT_THRESHOLD_DEFAULT,
                )
            }
        )

    # Clean up temporary ZUNIONSTORE key if we created one
    if resolved_path == "*" and lat_card >= 0:
        await store.delete_key(lat_key)

    obs.record_analytics_query(signal or "all", window, "hit", time.perf_counter() - _t0)
    return result.model_dump(exclude_none=True)
