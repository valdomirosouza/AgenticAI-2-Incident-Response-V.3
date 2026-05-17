# Spec LIM-02: HAProxy Analytics API

**Domain**: log-ingestion-and-metrics
**Owner**: SRE Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #59
**Linked ADRs**: ADR-0002, ADR-0011, ADR-0030, ADR-0033, ADR-0034, ADR-0035
**Review cadence**: On window change, percentile change, or response schema change

---

## 1. Purpose

Define the `GET /analytics` endpoint contract for the `log-ingestion-and-metrics` service:
the accepted query parameters, Redis query algorithm for exact percentile calculation,
response schema, window validation semantics, 404 conditions, and observability hooks.
This is the authoritative source for all analytics-side implementation decisions.

---

## 2. Context

The `DetectionAgent` queries `GET /analytics` to obtain the four Golden Signals
(Traffic, Error, Latency, Saturation) for a given backend path and time window.
This data drives anomaly detection and the `incident.created` trigger.

Redis Sorted Sets (ADR-0034) allow exact percentile retrieval via `ZRANK`/`ZCARD`
(ADR-0035) without any approximate sketching library. All data written by
`POST /ingestion` is immediately available for analytics queries within the same
time window bucket. TTLs (ADR-0030) govern automatic data expiry.

---

## 3. Decision

### 3.1 GET /analytics Endpoint Contract

**Method:** `GET`
**Path:** `/analytics`

**Query parameters:**

| Parameter     | Required | Type                                       | Default    | Validation                                     |
| ------------- | -------- | ------------------------------------------ | ---------- | ---------------------------------------------- |
| `backend`     | yes      | string                                     | —          | Non-empty; URL-decoded before Redis key lookup |
| `path`        | no       | string                                     | all paths  | URL-decoded; leading `/` normalised            |
| `signal`      | no       | `traffic\|error\|latency\|saturation`      | all        | Must be one of the four values if provided     |
| `window`      | no       | `1m\|5m\|15m\|1h`                          | `5m`       | Must be one of four values; 422 if invalid     |
| `percentiles` | no       | comma-separated integers (e.g. `50,95,99`) | `50,95,99` | Each value 1–99; duplicates removed            |

**Window to seconds mapping:**

| `window` | Seconds |
| -------- | ------- |
| `1m`     | 60      |
| `5m`     | 300     |
| `15m`    | 900     |
| `1h`     | 3600    |

**Window timestamp calculation:**

```python
window_secs  = WINDOW_MAP[window]   # e.g. 300 for "5m"
window_ts    = int(now.timestamp()) // window_secs * window_secs
```

`window_ts` is the floor of the current time aligned to the bucket boundary.
The endpoint always queries the **current** window bucket, not a historical range.

### 3.2 Response Schema

**Response 200 — data found:**

```json
{
  "backend": "web-servers",
  "path": "/api/v1/orders",
  "window": "5m",
  "window_start_iso": "2026-05-17T14:30:00Z",
  "traffic": {
    "total_requests": 1842,
    "rps": 6.14
  },
  "errors": {
    "rate_4xx": 0.012,
    "rate_5xx": 0.002,
    "total_4xx": 22,
    "total_5xx": 4
  },
  "latency_ms": {
    "p50": 32,
    "p95": 145,
    "p99": 412
  },
  "saturation": {
    "high_wait_pct": 3.2,
    "threshold_wait_ms": 50
  }
}
```

**Response 404 — no data:**

Returned when `lim:trx:{backend}:{path}:{window_ts}` does not exist in Redis
(key missing or TTL-expired). This means either no logs have been ingested for
this combination in the current window, or data has expired.

```json
{
  "detail": "No data for backend='web-servers' path='/api/v1/orders' window='5m'"
}
```

**Response 422 — invalid parameters:**

Returned when `window` is not one of `1m|5m|15m|1h`, or when an invalid `signal`
value is provided. FastAPI/Pydantic validation handles this automatically.

### 3.3 Field Definitions

| Response field                 | Source                                            | Formula                                                  |
| ------------------------------ | ------------------------------------------------- | -------------------------------------------------------- |
| `traffic.total_requests`       | `GET lim:trx:{backend}:{path}:{window_ts}`        | Integer value of counter                                 |
| `traffic.rps`                  | traffic / window_seconds                          | `round(total_requests / window_secs, 2)`                 |
| `errors.total_4xx`             | `GET lim:err4:{backend}:{path}:{window_ts}`       | Integer value of counter                                 |
| `errors.total_5xx`             | `GET lim:err5:{backend}:{path}:{window_ts}`       | Integer value of counter                                 |
| `errors.rate_4xx`              | total_4xx / total_requests                        | `round(total_4xx / total_requests, 4)` (0 if traffic=0)  |
| `errors.rate_5xx`              | total_5xx / total_requests                        | `round(total_5xx / total_requests, 4)` (0 if traffic=0)  |
| `latency_ms.p{k}`              | `ZRANGE lim:lat:{backend}:{path}:{window_ts} ...` | Exact percentile via ZRANK/ZCARD (section 3.4)           |
| `saturation.high_wait_pct`     | lim:sat / lim:trx × 100                           | `round(sat_count / total_requests * 100, 1)`             |
| `saturation.threshold_wait_ms` | `SAT_WAIT_THRESHOLD_MS` env var                   | Config value at query time (default 50)                  |
| `window_start_iso`             | window_ts                                         | `datetime.utcfromtimestamp(window_ts).isoformat() + "Z"` |

### 3.4 Exact Percentile Calculation (ADR-0035)

Percentiles are computed from the Redis Sorted Set `lim:lat:{backend}:{path}:{window_ts}`.
The Sorted Set stores one member per ingested log entry with `score = timers.total_time`.

Algorithm:

```python
def query_percentile(redis, key: str, p: int) -> float:
    card = redis.zcard(key)          # total number of entries
    if card == 0:
        return 0.0
    rank = math.ceil(p / 100 * card) - 1   # 0-based rank
    rank = max(0, min(rank, card - 1))      # clamp to valid range
    result = redis.zrange(key, rank, rank, withscores=True)
    return result[0][1] if result else 0.0
```

This is exact (not approximate). No DDSketch, t-digest, or HDR Histogram is used.
The bounded dataset size per TTL window makes exact computation feasible (ADR-0035).

**Examples:**

| `ZCARD` | Percentile | `rank = ceil(p/100 * card) - 1` | Value returned       |
| ------- | ---------- | ------------------------------- | -------------------- |
| 1       | P99        | `ceil(0.99 * 1) - 1 = 0`        | The only entry       |
| 100     | P50        | `ceil(0.50 * 100) - 1 = 49`     | 50th smallest value  |
| 100     | P99        | `ceil(0.99 * 100) - 1 = 98`     | 99th smallest value  |
| 1000    | P95        | `ceil(0.95 * 1000) - 1 = 949`   | 950th smallest value |

### 3.5 Multi-Path Aggregation

When `path` is omitted, the endpoint returns metrics aggregated across **all paths**
for the given `backend` and `window`. Aggregation rules:

| Signal     | Aggregation method                                                            |
| ---------- | ----------------------------------------------------------------------------- |
| Traffic    | Sum of all `lim:trx:{backend}:*:{window_ts}` counters                         |
| Errors 4xx | Sum of all `lim:err4:{backend}:*:{window_ts}` counters                        |
| Errors 5xx | Sum of all `lim:err5:{backend}:*:{window_ts}` counters                        |
| Latency    | `ZUNIONSTORE` to a temporary key; percentile from merged set; delete temp key |
| Saturation | Sum of all `lim:sat:{backend}:*:{window_ts}` counters                         |

Rates are recalculated from the aggregated totals (not averaged from individual rates).
`path` field in response is `"*"` when aggregation is active.

The `SCAN` pattern `lim:trx:{backend}:*:{window_ts}` is used to discover paths;
results are collected before pipeline execution to avoid blocking the event loop.

### 3.6 Signal Filtering

When `signal` is provided, only the corresponding section of the response is populated.
All other signal fields are omitted from the response JSON (not null, not 0 — absent).

| `signal` value | Fields included in response     |
| -------------- | ------------------------------- |
| `traffic`      | `traffic`                       |
| `error`        | `errors`                        |
| `latency`      | `latency_ms`                    |
| `saturation`   | `saturation`                    |
| _(omitted)_    | All four signal fields included |

### 3.7 Observability

OTel histogram emitted per analytics call:

| Metric                        | Labels                           | Recorded when           |
| ----------------------------- | -------------------------------- | ----------------------- |
| `lim_analytics_query_seconds` | `signal={all,traffic,error,...}` | Per GET /analytics call |
|                               | `window={1m,5m,15m,1h}`          |                         |
|                               | `result={hit,miss}`              |                         |

`result=miss` corresponds to a 404 response. `result=hit` corresponds to a 200.

### 3.8 Health Endpoints

| Path            | Method | Response 200          | Response 503                                  |
| --------------- | ------ | --------------------- | --------------------------------------------- |
| `/health/live`  | GET    | `{"status": "alive"}` | Never (liveness always returns 200)           |
| `/health/ready` | GET    | `{"status": "ready"}` | `{"status": "not_ready"}` if Redis PING fails |

Readiness check: `redis.ping()` must succeed within 200ms. Failure returns 503.

---

## 4. Acceptance Criteria

- [ ] `GET /analytics?backend=web-servers&window=5m` returns 200 with all four signal sections when data exists
- [ ] `GET /analytics?backend=web-servers&signal=latency&window=5m` returns 200 with only `latency_ms` section — `traffic`, `errors`, `saturation` absent from response
- [ ] `GET /analytics?backend=missing&window=5m` returns 404 with detail message
- [ ] `GET /analytics?backend=web-servers&window=bad` returns 422
- [ ] `GET /analytics?backend=web-servers&window=1h&percentiles=50,95,99` returns `latency_ms` keys `p50`, `p95`, `p99`
- [ ] `GET /analytics?backend=web-servers&window=5m` with `path` omitted returns `"path": "*"` and aggregated metrics
- [ ] Latency P99 returned for a 2-entry Sorted Set `[48, 512]` equals `512`
- [ ] Latency P50 returned for a 2-entry Sorted Set `[48, 512]` equals `512` (ceil(0.5 * 2) - 1 = 0 → rank 0 → 48 is wrong; correct: rank = max(0, ceil(0.5*2)-1) = max(0, 0) = 0 → 48)
- [ ] `traffic.rps` equals `total_requests / window_seconds` rounded to 2 decimal places
- [ ] `saturation.high_wait_pct` is `0.0` when no entries exceeded `SAT_WAIT_THRESHOLD_MS`
- [ ] `GET /health/live` returns 200 regardless of Redis state
- [ ] `GET /health/ready` returns 503 when Redis is unavailable
- [ ] `lim_analytics_query_seconds{result="miss"}` increments on 404 response
- [ ] `lim_analytics_query_seconds{result="hit"}` increments on 200 response
- [ ] Import-linter: `log_ingestion.domain` has zero imports from `log_ingestion.adapters` or `log_ingestion.api`

---

## 5. Linked ADRs

| ADR      | Decision                          | Relevance to this spec                                              |
| -------- | --------------------------------- | ------------------------------------------------------------------- |
| ADR-0002 | Hexagonal Architecture            | `analytics.py` router calls port; port implemented by Redis adapter |
| ADR-0011 | Golden Signals                    | Defines the four signals returned per analytics query               |
| ADR-0030 | Data retention TTL                | 404 can occur when TTL expires; response documents this             |
| ADR-0033 | Service location (`services/`)    | Service lives in `services/log-ingestion-and-metrics/`              |
| ADR-0034 | Redis Sorted Sets for percentiles | `ZRANGE` used for latency percentile retrieval                      |
| ADR-0035 | Exact percentile via ZRANK        | Algorithm in section 3.4 is the canonical implementation            |
