# Spec LIM-01: HAProxy Log Ingestion API

**Domain**: log-ingestion-and-metrics
**Owner**: SRE Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #59
**Linked ADRs**: ADR-0002, ADR-0011, ADR-0013, ADR-0014, ADR-0028, ADR-0030, ADR-0033, ADR-0034, ADR-0035
**Review cadence**: On schema change or batch limit change

---

## 1. Purpose

Define the `POST /ingestion` endpoint contract for the `log-ingestion-and-metrics` service:
the accepted HAProxy JSON log schema, path extraction rules, PII masking requirements,
batch semantics, Golden Signal extraction logic, Redis storage layout, and partial-failure
behaviour. This is the authoritative source for all ingestion-side implementation decisions.

---

## 2. Context

HAProxy is the ingress layer of the platform. It emits one structured JSON log entry per
HTTP request. The Incident Response Copilot's `DetectionAgent` needs near-real-time access
to the four Golden Signals (Traffic, Error, Latency, Saturation) per backend path to detect
anomalies and trigger `incident.created`. Without an ingestion pipeline that normalises and
stores these signals efficiently, the DetectionAgent must rely on Prometheus scrape cycles
alone, increasing MTTD.

The schema was confirmed by the platform team. `client_ip` is PII under LGPD art. 5 I and
GDPR art. 4(1); it must never reach any persistent store without masking. All four Golden
Signals can be derived from the confirmed fields without schema changes.

---

## 3. Decision

### 3.1 Confirmed HAProxy JSON Schema

Every request produces exactly one log entry with the following structure:

```json
{
  "timestamp": "2024-06-20T15:56:09",
  "client_ip": "192.168.1.50",
  "client_port": 44321,
  "frontend": "http-in",
  "backend": "web-servers",
  "server": "web-01",
  "status_code": 200,
  "bytes_read": 1450,
  "request": "GET /api/v1/data HTTP/1.1",
  "termination_state": "--",
  "timers": {
    "total_time": 105,
    "wait": 2,
    "connect": 1,
    "response": 102
  }
}
```

**Field types and semantics:**

| Field               | Type            | Semantic                                                         |
| ------------------- | --------------- | ---------------------------------------------------------------- |
| `timestamp`         | ISO 8601 string | Request completion time                                          |
| `client_ip`         | string          | **PII** — originating client IP                                  |
| `client_port`       | integer         | Ephemeral source port                                            |
| `frontend`          | string          | HAProxy frontend name                                            |
| `backend`           | string          | HAProxy backend name — primary metric namespace key              |
| `server`            | string          | Backend server that handled the request                          |
| `status_code`       | integer         | HTTP response status code                                        |
| `bytes_read`        | integer         | Response body size in bytes                                      |
| `request`           | string          | Full HTTP request line: `"METHOD /path[?query] HTTP/x.x"`        |
| `termination_state` | string          | `"--"` = clean termination; any other value = abnormal           |
| `timers.total_time` | integer (ms)    | Total request duration (Tt) — **primary latency metric**         |
| `timers.wait`       | integer (ms)    | Time request waited in backend queue (Tw) — **saturation proxy** |
| `timers.connect`    | integer (ms)    | TCP connection time to backend (Tc)                              |
| `timers.response`   | integer (ms)    | Backend server processing time (Tr)                              |

### 3.2 Path Extraction

The `request` field contains the full HTTP request line. Path is extracted as follows:

```python
method, raw_path, _ = entry.request.split(" ", 2)
path = raw_path.split("?")[0]   # strip query string
```

Examples:

| `request` field                         | Extracted `method` | Extracted `path`   |
| --------------------------------------- | ------------------ | ------------------ |
| `GET /api/v1/orders HTTP/1.1`           | `GET`              | `/api/v1/orders`   |
| `POST /api/v1/users?dry_run=1 HTTP/1.1` | `POST`             | `/api/v1/users`    |
| `DELETE /api/v1/items/42 HTTP/1.1`      | `DELETE`           | `/api/v1/items/42` |

The combination `backend + path` forms the metric namespace key. `backend` alone is the
mandatory grouping dimension; `path` adds finer granularity when present.

### 3.3 PII Masking (ADR-0014, ADR-0028)

`client_ip` **must never be written to any persistent store** (Redis, logs, traces).
Before any MetricPoint is constructed, the IP is replaced by a 16-character hex digest:

```python
masked_ip = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
```

The masked value is not stored either — it is used only for within-request deduplication
if needed. No raw IP value may appear in any Redis key, counter, log line, or OTel span
attribute. Violation triggers harness gate G09 (custom-rule-raw-log-pii).

### 3.4 Golden Signal Extraction

Each log entry produces exactly **four MetricPoints**, one per signal:

| Signal         | Source field(s)                    | Value                           | Condition                                           |
| -------------- | ---------------------------------- | ------------------------------- | --------------------------------------------------- |
| **TRAFFIC**    | count                              | `1`                             | Always                                              |
| **ERROR**      | `status_code`, `termination_state` | `1` if error, `0` otherwise     | `status_code >= 400` OR `termination_state != "--"` |
| **LATENCY**    | `timers.total_time`                | `total_time` (ms)               | Always                                              |
| **SATURATION** | `timers.wait`                      | `1` if saturated, `0` otherwise | `timers.wait > SAT_WAIT_THRESHOLD_MS`               |

`SAT_WAIT_THRESHOLD_MS` defaults to `50` ms and is configurable via environment variable
`LIM_SAT_THRESHOLD_MS`. A wait time exceeding this threshold indicates the backend queue
is under pressure.

Error classification details:

| Condition                                             | ERROR value | Rationale                                                                            |
| ----------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------ |
| `status_code` in 400–499                              | `1`         | Client error — counted as 4xx                                                        |
| `status_code` in 500–599                              | `1`         | Server error — counted as 5xx                                                        |
| `termination_state != "--"`                           | `1`         | Abnormal connection termination (e.g., `"SD"` = server down, `"sD"` = slow response) |
| `status_code` 200–399 AND `termination_state == "--"` | `0`         | Clean request                                                                        |

### 3.5 Time Window Bucketing

All MetricPoints are assigned to a time window bucket:

```python
window_ts = int(entry.timestamp.timestamp()) // window_seconds * window_seconds
```

Supported windows: `60` (1m), `300` (5m), `900` (15m), `3600` (1h).
`window_ts` is the bucket floor timestamp (Unix epoch, integer).

### 3.6 Redis Storage Layout (ADR-0034, ADR-0035)

**Namespace prefix:** `lim:` (Log-Ingestion-Metrics)

| Signal     | Redis type | Key pattern                             | Operation                           | TTL (ADR-0030) |
| ---------- | ---------- | --------------------------------------- | ----------------------------------- | -------------- |
| LATENCY    | Sorted Set | `lim:lat:{backend}:{path}:{window_ts}`  | `ZADD score=total_time member=uuid` | 86400s (24 h)  |
| TRAFFIC    | String     | `lim:trx:{backend}:{path}:{window_ts}`  | `INCR`                              | 604800s (7 d)  |
| ERROR 4xx  | String     | `lim:err4:{backend}:{path}:{window_ts}` | `INCR`                              | 604800s (7 d)  |
| ERROR 5xx  | String     | `lim:err5:{backend}:{path}:{window_ts}` | `INCR`                              | 604800s (7 d)  |
| SATURATION | String     | `lim:sat:{backend}:{path}:{window_ts}`  | `INCR` (when wait > threshold)      | 604800s (7 d)  |

All writes for a single batch are executed in a single Redis pipeline for atomicity.
`EXPIRE` is set on every key unconditionally (refreshes TTL on each write).

Key sanitisation: `backend` and `path` values are URL-encoded before use as key segments
to prevent key injection via crafted backend names or paths containing `:`.

### 3.7 POST /ingestion Endpoint Contract

**Method:** `POST`
**Path:** `/ingestion`
**Content-Type:** `application/json`

**Accepted bodies:**

Single entry (object):

```json
{ "timestamp": "...", "client_ip": "...", ... }
```

Batch (array, maximum 1000 entries):

```json
[{ ... }, { ... }]
```

**Response 202 Accepted:**

```json
{
  "accepted": 3,
  "rejected": 0,
  "errors": []
}
```

**Partial-failure semantics:**

- The endpoint never returns `4xx` for validation errors in individual entries.
- Entries that fail Pydantic validation are counted in `rejected`; their error message is
  appended to `errors` (max 10 error strings to cap response size).
- Entries that pass validation are processed and stored regardless of sibling failures.
- Redis write failures raise `MetricStoreError` and increment `lim_ingestion_events_total{result="store_error"}`.

**Batch size limit:**
`HaproxyLogBatch` enforces `max_length=1000` at the Pydantic model level. Batches exceeding
this limit receive `422 Unprocessable Entity` before any processing occurs.

### 3.8 Observability

OTel counters emitted per ingestion call:

| Metric                        | Labels                                                 | Incremented when  |
| ----------------------------- | ------------------------------------------------------ | ----------------- |
| `lim_ingestion_events_total`  | `backend`, `result={accepted,parse_error,store_error}` | Per entry outcome |
| `lim_ingestion_batches_total` | `size_bucket={1-10,11-100,101-1000}`                   | Per batch call    |

---

## 4. Acceptance Criteria

- [ ] `POST /ingestion` with 3 valid entries returns `202 {"accepted": 3, "rejected": 0, "errors": []}`
- [ ] `POST /ingestion` with 1 invalid + 2 valid returns `202 {"accepted": 2, "rejected": 1, "errors": [...]}`
- [ ] `POST /ingestion` with 1001 entries returns `422` without processing any entry
- [ ] `client_ip` is absent from all Redis keys, log lines, OTel span attributes, and API responses
- [ ] `termination_state` value `"SD"` is classified as ERROR=1 regardless of `status_code`
- [ ] `timers.wait = 80` (> default 50 ms threshold) produces SATURATION MetricPoint value=1
- [ ] `timers.wait = 10` (< default 50 ms threshold) produces SATURATION MetricPoint value=0
- [ ] Path `"/api/v1/data?q=1"` extracted from request `"GET /api/v1/data?q=1 HTTP/1.1"` → stored as `"/api/v1/data"`
- [ ] Redis key TTL for latency sorted set ≤ 86400 seconds after write
- [ ] Redis key TTL for traffic counter ≤ 604800 seconds after write
- [ ] All writes for a batch executed in a single Redis pipeline
- [ ] `lim_ingestion_events_total{result="accepted"}` increments for each accepted entry
- [ ] Import-linter: `log_ingestion.domain` has zero imports from `log_ingestion.adapters` or `log_ingestion.api`
- [ ] Import-linter: `log_ingestion.adapters` has zero imports from `log_ingestion.api`

---

## 5. Linked ADRs

| ADR      | Decision                              | Relevance to this spec                                                |
| -------- | ------------------------------------- | --------------------------------------------------------------------- |
| ADR-0002 | Hexagonal Architecture                | Service structure: domain → ports → adapters; import-linter contracts |
| ADR-0011 | Golden Signals                        | Defines the four signals extracted per log entry                      |
| ADR-0013 | Structured JSON logging               | Log output format for the service's own logs                          |
| ADR-0014 | PII masking in logs and traces        | `client_ip` must never reach persistent store                         |
| ADR-0028 | PII sanitization before external APIs | Extends PII gate to Redis writes and OTel exports                     |
| ADR-0030 | Data retention TTL                    | Latency sorted sets 24 h; counters 7 d                                |
| ADR-0033 | Service location (`services/`)        | Why this service lives in monorepo `services/` directory              |
| ADR-0034 | Redis Sorted Sets for percentiles     | Redis chosen over InfluxDB/TimescaleDB                                |
| ADR-0035 | Exact percentile via ZRANK            | ZRANK/ZCARD exact method chosen over DDSketch/t-digest                |
