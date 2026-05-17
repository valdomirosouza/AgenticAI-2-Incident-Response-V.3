# Skill: Dashboards

**Domain**: observability
**Activation triggers**: Dashboard, Grafana, NOC dashboard, engineering dashboard, CUJ dashboard, panel, visualization, on-call dashboard, SLO dashboard
**References**: specs/observability/08-golden-signals.md, specs/observability/11-slo-definitions.md, ADR-0011

---

## Dashboard Hierarchy

Three dashboard tiers serve different audiences:

| Dashboard       | Audience          | Refresh rate | Focus                                          |
| --------------- | ----------------- | ------------ | ---------------------------------------------- |
| **NOC**         | NOC operators     | 15s          | Active incidents, Golden Signals, alert status |
| **Engineering** | On-call engineers | 30s          | Agent internals, HITL queue, LLM performance   |
| **CUJ**         | Engineering leads | 5m           | User-facing SLO health, error budget           |

---

## NOC Dashboard — Panel Inventory

Audience: NOC operators monitoring active incidents in real time.

### Row 1 — Incident Status

| Panel            | Type  | Query                                                     |
| ---------------- | ----- | --------------------------------------------------------- | ------ |
| Active incidents | Stat  | `count(incident_active{severity=~"P1                      | P2"})` |
| P1 incident list | Table | Latest `incident.created` audit events with severity = P1 |
| MTTD (current)   | Gauge | `incident:mttd_mean_30d` vs 5-min target                  |
| MTTR (current)   | Gauge | `incident:mttr_mean_30d` vs 30-min target                 |

### Row 2 — Golden Signals

| Panel          | Type        | Query                                                                      |
| -------------- | ----------- | -------------------------------------------------------------------------- |
| Error rate     | Time series | `rate(http_requests_errors_total[5m]) / rate(http_requests_total[5m])`     |
| Latency p99    | Time series | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| Traffic (RPS)  | Time series | `rate(http_requests_total[5m])`                                            |
| CPU saturation | Time series | `rate(container_cpu_usage_seconds_total[5m]) * 100`                        |

### Row 3 — Alert Status

| Panel         | Type       | Content                                                          |
| ------------- | ---------- | ---------------------------------------------------------------- |
| Firing alerts | Alert list | All alerts in `firing` state                                     |
| SLO burn rate | Stat       | Current multi-window burn rate vs. threshold (P1: 14.4×, P2: 6×) |

---

## Engineering Dashboard — Panel Inventory

Audience: on-call engineers during active incidents.

### Row 1 — Agent Pipeline

| Panel                     | Type        | Query / Source                                                                |
| ------------------------- | ----------- | ----------------------------------------------------------------------------- |
| Detection agent latency   | Time series | `histogram_quantile(0.99, rate(detection_agent_duration_seconds_bucket[5m]))` |
| Triage agent latency      | Time series | Same pattern for `triage_agent_*`                                             |
| RCA agent latency         | Time series | Same pattern for `rca_agent_*`                                                |
| Remediation agent latency | Time series | Same pattern for `remediation_agent_*`                                        |

### Row 2 — HITL / Guardrails

| Panel                        | Type  | Query                                         |
| ---------------------------- | ----- | --------------------------------------------- |
| HITL queue depth             | Gauge | `hitl_queue_depth`                            |
| HITL timeout rate            | Stat  | `rate(hitl_timeouts_total[1h])`               |
| HITL validation failures     | Stat  | `rate(hitl_validation_failures_total[1h])`    |
| Kill-switch activations (7d) | Stat  | `increase(kill_switch_activations_total[7d])` |

### Row 3 — LLM Performance

| Panel                          | Type        | Query                                                                     |
| ------------------------------ | ----------- | ------------------------------------------------------------------------- |
| LLM request latency p99        | Time series | `histogram_quantile(0.99, rate(llm_request_duration_seconds_bucket[5m]))` |
| LLM schema validation failures | Time series | `rate(llm_schema_validation_failures_total[5m])`                          |
| LLM token budget used          | Gauge       | `llm_token_budget_used_ratio`                                             |
| PII masking events/min         | Time series | `rate(pii_masked_total[1m])`                                              |

### Row 4 — Audit Trail Health

| Panel                    | Type  | Query                                   |
| ------------------------ | ----- | --------------------------------------- |
| Audit write success rate | Stat  | Must be 100% — any drop is a P1 trigger |
| Audit write lag          | Gauge | `audit_trail_write_lag_seconds`         |

---

## CUJ Dashboard — Panel Inventory

Audience: engineering leads tracking user-facing service health and SLO compliance.

### Row 1 — SLO Health

| Panel                  | Type  | Query / SLI                                                      |
| ---------------------- | ----- | ---------------------------------------------------------------- |
| SLO compliance (30d)   | Stat  | % of time all SLIs within target over last 30 days               |
| Error budget remaining | Gauge | `1 - (error_budget_consumed / error_budget_total)` per SLO       |
| MTTD improvement       | Stat  | `(mttd_baseline - incident:mttd_mean_30d) / mttd_baseline * 100` |
| MTTR improvement       | Stat  | `(mttr_baseline - incident:mttr_mean_30d) / mttr_baseline * 100` |

### Row 2 — SLI Detail

| Panel           | Type        | SLI    | Target      |
| --------------- | ----------- | ------ | ----------- |
| Detection SLI   | Time series | SLI-01 | P1 < 5 min  |
| Triage SLI      | Time series | SLI-02 | P1 < 2 min  |
| RCA SLI         | Time series | SLI-03 | P1 < 10 min |
| Remediation SLI | Time series | SLI-04 | P1 < 15 min |

---

## Dashboard Design Rules

1. **No raw PromQL on dashboards** — use recording rules (`incident:mttd_mean_30d`) for any expression used in more than one panel.
2. **No PII** — panel titles, labels, and queries must not include user IDs, emails, or real service names. Use `svc_<category>_<N>` labels.
3. **Thresholds match spec 11** — alert thresholds visualized in panels must match the PromQL alerts exactly.
4. **Red = actionable** — red only for conditions that require immediate human action (P1). Yellow for degraded. Green for healthy.
5. **Link to runbook** — every alert panel includes a link to the relevant runbook in `docs/runbooks/`.
6. **Dashboard as code** — all dashboards are defined in `infrastructure/monitoring/grafana/` as JSON and deployed via Terraform. No manual dashboard changes in production.

---

## Grafana Variable Convention

Use these template variables for filtering across all dashboards:

| Variable    | Values                           | Used in                            |
| ----------- | -------------------------------- | ---------------------------------- |
| `$env`      | `production`, `staging`, `local` | All dashboards                     |
| `$service`  | All service names                | Engineering dashboard              |
| `$severity` | `P1`, `P2`, `P3`, `P4`           | NOC and CUJ dashboards             |
| `$incident` | Active incident IDs              | Engineering dashboard (drill-down) |
