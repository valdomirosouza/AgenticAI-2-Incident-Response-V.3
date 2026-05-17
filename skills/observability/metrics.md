# Skill: Metrics

**Domain**: observability
**Activation triggers**: Metrics, alerting, Golden Signals, SLO thresholds, Prometheus, PromQL, recording rules, error budget, burn rate, saturation, latency, error rate, traffic
**References**: specs/observability/08-golden-signals.md, specs/observability/11-slo-definitions.md, ADR-0011, ADR-0015

---

## Golden Signals (ADR-0011)

The four Golden Signals are the canonical metric set. Every service must expose all four.

| Signal         | Definition                                                  | Prometheus metric pattern                               |
| -------------- | ----------------------------------------------------------- | ------------------------------------------------------- |
| **Latency**    | Time to serve a request — distinguish successful vs. failed | `*_duration_seconds{quantile="0.99"}`                   |
| **Error rate** | Proportion of requests that result in an error              | `rate(*_errors_total[5m]) / rate(*_requests_total[5m])` |
| **Traffic**    | Demand placed on the system (requests/s, events/s)          | `rate(*_requests_total[5m])`                            |
| **Saturation** | How "full" the service is — proxy for remaining capacity    | CPU%, memory%, queue depth, token budget                |

---

## SLO Targets by Tier (spec 08 + spec 11)

### Latency

| Tier     | p50 target | p95 target | p99 target |
| -------- | ---------- | ---------- | ---------- |
| Critical | < 200 ms   | < 500 ms   | < 1 s      |
| Standard | < 500 ms   | < 1 s      | < 2 s      |
| Internal | < 1 s      | < 3 s      | < 5 s      |

### LLM-specific latency

| Metric                              | Target |
| ----------------------------------- | ------ |
| `llm_request_duration_seconds{p50}` | < 3 s  |
| `llm_request_duration_seconds{p99}` | < 10 s |

### Error rate thresholds

| Severity trigger | Error rate condition                |
| ---------------- | ----------------------------------- |
| P1               | > 50% error rate OR complete outage |
| P2               | > 5% on Critical tier               |
| P3               | Non-critical service degraded       |
| P4               | Informational anomaly               |

### Saturation thresholds

| Resource              | Warning | Critical |
| --------------------- | ------- | -------- |
| CPU                   | > 70%   | > 85%    |
| Memory                | > 75%   | > 90%    |
| Disk                  | > 70%   | > 85%    |
| LLM token budget      | > 80%   | > 95%    |
| HITL queue depth      | > 3     | > 5      |
| Audit trail write lag | > 2 s   | > 5 s    |

---

## Prometheus Naming Convention

```
<service>_<unit>_<type>[_total]

Examples:
  triage_agent_request_duration_seconds   (histogram)
  remediation_agent_actions_total         (counter)
  hitl_queue_depth                        (gauge)
  llm_request_duration_seconds            (histogram)
  llm_schema_validation_failures_total    (counter)
  audit_trail_write_lag_seconds           (gauge)
```

| Suffix      | Metric type   | When to use                              |
| ----------- | ------------- | ---------------------------------------- |
| `_total`    | Counter       | Monotonically increasing counts          |
| `_seconds`  | Histogram     | Duration measurements                    |
| `_ratio`    | Gauge         | Proportions (0.0 – 1.0)                  |
| `_bytes`    | Gauge/Counter | Memory, payload sizes                    |
| (no suffix) | Gauge         | Current state values (queue depth, etc.) |

---

## Recording Rules (spec 11)

Always use recording rules for frequently-queried expressions — never inline complex PromQL in dashboards.

```promql
# MTTD per incident (seconds)
record: incident:mttd_seconds
expr: (
  timestamp(audit_event_timestamp{event="incident.created"})
  - timestamp(audit_event_timestamp{event="first_anomaly_sample"})
)

# MTTR per incident (seconds)
record: incident:mttr_seconds
expr: (
  timestamp(audit_event_timestamp{event="incident.resolved"})
  - timestamp(audit_event_timestamp{event="incident.created"})
)

# Rolling 30-day mean MTTD
record: incident:mttd_mean_30d
expr: avg_over_time(incident:mttd_seconds[30d])

# Rolling 30-day mean MTTR
record: incident:mttr_mean_30d
expr: avg_over_time(incident:mttr_seconds[30d])

# LLM schema validation failure rate (alert if > 5%)
record: llm:schema_validation_failure_rate_5m
expr: (
  rate(llm_schema_validation_failures_total[5m])
  / rate(llm_requests_total[5m])
)
```

---

## Multi-Window Burn Rate Alerting (ADR-0015)

SLO-based alerting uses multi-window burn rates — no fixed-threshold alerts.

| Window | Burn rate | Severity | Action            |
| ------ | --------- | -------- | ----------------- |
| 1h/5m  | > 14.4×   | P1       | Page immediately  |
| 6h/30m | > 6×      | P1       | Page immediately  |
| 1d/2h  | > 3×      | P2       | Page within 5 min |
| 3d/6h  | > 1×      | P3       | Ticket + Slack    |

```promql
# Example: P1 burn rate alert (1h window, burn rate > 14.4×)
alert: SLOBurnRateP1
expr: (
  rate(http_requests_errors_total[1h]) / rate(http_requests_total[1h])
) > (14.4 * (1 - 0.999))
for: 2m
labels:
  severity: P1
annotations:
  summary: "SLO burn rate P1 — error budget exhausting at 14.4× rate"
```

---

## On-Call Trigger Conditions (spec 11)

Page on-call automatically when:

1. P1 burn rate alert fires (1h or 6h window)
2. Audit trail write success rate < 100% (any failure)
3. HITL queue depth > 5 (approval bottleneck)
4. LLM schema validation failure rate > 5% for 10 min
5. Kill-switch activated (`agent.kill_switch_activated` event)
6. Two consecutive remediation failures for same incident
7. `incident:mttd_mean_30d` exceeds P1 target (< 5 min) for 7 consecutive days

---

## Metric Instrumentation (Python — OpenTelemetry)

```python
from opentelemetry import metrics

meter = metrics.get_meter("triage-agent")

# Histogram for latency
classify_duration = meter.create_histogram(
    name="triage_agent_classify_duration_seconds",
    description="Time to classify incident severity",
    unit="s",
)

# Counter for errors
classification_errors = meter.create_counter(
    name="triage_agent_classification_errors_total",
    description="Number of classification failures",
)

# Gauge for queue depth
hitl_queue = meter.create_observable_gauge(
    name="hitl_queue_depth",
    description="Number of pending HITL approvals",
    callbacks=[lambda _: hitl_service.queue_depth()],
)

# Usage in use case:
with classify_duration.record_duration():
    result = classify_severity(metrics=current_metrics)
```
