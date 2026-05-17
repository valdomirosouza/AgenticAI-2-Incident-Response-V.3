# Spec 11: SLO Definitions

**Domain**: observability
**Owner**: SRE Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #11
**Linked ADRs**: ADR-0015
**Review cadence**: Quarterly or on SLO change

---

## 1. Purpose

Define SLO/SLI/SLA per service, error budget policy, multi-window multi-burn-rate alert
thresholds and on-call trigger conditions. These definitions are the authoritative source
for alert rule configuration in Prometheus and the staging gate validation.

---

## 2. Context

ADR-0015 adopted multi-window multi-burn-rate alerting as the SLO alerting strategy.
The DetectionAgent uses SLO breach signals as a primary source for `incident.created`
(spec 03). Without explicit SLO targets and burn rate thresholds, the alerting layer
cannot distinguish a P1 emergency from background noise — and MTTD cannot be measured
against a defined target.

---

## 3. Decision

### 3.1 SLI definitions

| SLI ID | Name                | Measurement                                                   | Good event definition                                              |
| ------ | ------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------ |
| SLI-01 | Availability        | Ratio of successful HTTP responses to total requests          | `status_code` not in `{500, 502, 503, 504}`                        |
| SLI-02 | Latency (p99)       | 99th percentile request duration                              | `http_request_duration_seconds` p99 ≤ tier threshold               |
| SLI-03 | LLM Success Rate    | Ratio of LLM calls returning valid schema-validated response  | No `llm_schema_validation_failures_total` increment                |
| SLI-04 | HITL Responsiveness | Ratio of HITL approvals received within the P-severity window | Approval received before `hitl_approval_timeouts_total` increments |
| SLI-05 | Audit Trail Write   | Ratio of audit events successfully written to the hash chain  | No `audit.write_failed` events                                     |

### 3.2 SLO targets per service

#### Critical tier (OrchestratorAgent API, HITL endpoint)

| SLO                            | Target | Measurement window | Error budget (30 days) |
| ------------------------------ | ------ | ------------------ | ---------------------- |
| SLO-C01 Availability           | 99.9%  | 30-day rolling     | 43.8 min/month         |
| SLO-C02 Latency p99 ≤ 1 000 ms | 99.0%  | 30-day rolling     | 7.2 h/month            |
| SLO-C03 Audit Trail Write      | 100.0% | 30-day rolling     | 0 min (zero-tolerance) |

SLO-C03 is zero-tolerance: any audit trail write failure triggers an immediate P1
incident regardless of burn rate — the integrity of the audit chain cannot be degraded.

#### Standard tier (Specialist Agents)

| SLO                            | Target | Measurement window | Error budget (30 days) |
| ------------------------------ | ------ | ------------------ | ---------------------- |
| SLO-S01 Availability           | 99.5%  | 30-day rolling     | 3.6 h/month            |
| SLO-S02 Latency p99 ≤ 5 000 ms | 95.0%  | 30-day rolling     | 36 h/month             |
| SLO-S03 LLM Success Rate       | 98.0%  | 30-day rolling     | 14.4 h/month           |
| SLO-S04 HITL Responsiveness    | 95.0%  | 30-day rolling     | 36 h/month             |

#### Internal tier (Observability stack)

| SLO                    | Target | Measurement window | Error budget (30 days) |
| ---------------------- | ------ | ------------------ | ---------------------- |
| SLO-I01 Availability   | 99.0%  | 30-day rolling     | 7.2 h/month            |
| SLO-I02 Scrape success | 99.5%  | 30-day rolling     | 3.6 h/month            |

### 3.3 Multi-window multi-burn-rate alert thresholds

Per ADR-0015. Burn rate = (error rate) / (1 − SLO target).

#### Critical tier — SLO-C01 Availability (99.9%)

| Alert window | Burn rate threshold | Budget consumed | Severity | Page?             |
| ------------ | ------------------- | --------------- | -------- | ----------------- |
| 1h / 5m      | 14.4×               | 100% in 1h      | **P1**   | Immediate         |
| 6h / 30m     | 6×                  | 100% in 6h      | **P2**   | Page within 5 min |
| 24h / 2h     | 3×                  | 100% in 24h     | **P3**   | Ticket + Slack    |
| 72h / 6h     | 1×                  | 100% in 72h     | **P4**   | Ticket only       |

Prometheus alert rule pattern (P1):

```promql
(
  sum(rate(http_requests_total{service="orchestrator",status_code=~"5.."}[1h]))
  /
  sum(rate(http_requests_total{service="orchestrator"}[1h]))
) > (14.4 * 0.001)
AND
(
  sum(rate(http_requests_total{service="orchestrator",status_code=~"5.."}[5m]))
  /
  sum(rate(http_requests_total{service="orchestrator"}[5m]))
) > (14.4 * 0.001)
```

#### Standard tier — SLO-S01 Availability (99.5%)

| Alert window | Burn rate threshold | Budget consumed | Severity | Page?             |
| ------------ | ------------------- | --------------- | -------- | ----------------- |
| 1h / 5m      | 14.4×               | 100% in 1h      | **P1**   | Immediate         |
| 6h / 30m     | 6×                  | 100% in 6h      | **P2**   | Page within 5 min |
| 24h / 2h     | 3×                  | 100% in 24h     | **P3**   | Ticket + Slack    |

### 3.4 Error budget policy

| Budget consumed in 30 days | Action                                                          |
| -------------------------- | --------------------------------------------------------------- |
| 0–25%                      | No action; system operating within normal parameters            |
| 25–50%                     | Engineering review: identify trend; plan reliability work       |
| 50–75%                     | Feature freeze on non-reliability work; SRE leads investigation |
| 75–100%                    | Full reliability incident declared; all new `feat` PRs blocked  |
| 100% (budget exhausted)    | SLA breach review; incident post-mortem required within 5 days  |

Error budget consumption is tracked via Prometheus recording rules and displayed on the
NOC dashboard. The staging gate (`harness/staging-check.yml`) blocks production deploy
if error budget consumption > 75% for any Critical-tier SLO.

### 3.5 SLA commitments

For this research prototype, no external SLA is committed. Internal SLA targets for
planning purposes:

| Service tier | Internal SLA  | Measurement basis |
| ------------ | ------------- | ----------------- |
| Critical     | 99.9% monthly | SLO-C01           |
| Standard     | 99.5% monthly | SLO-S01           |
| Internal     | 99.0% monthly | SLO-I01           |

### 3.6 On-call trigger conditions

| Condition                                  | Severity | Action                                            |
| ------------------------------------------ | -------- | ------------------------------------------------- |
| P1 burn rate breach (14.4× in 1h AND 5m)   | P1       | Page primary on-call immediately                  |
| P2 burn rate breach (6× in 6h AND 30m)     | P2       | Page primary on-call within 5 minutes             |
| Audit trail write failure (any occurrence) | P1       | Page primary on-call immediately (zero-tolerance) |
| HITL approval timeout (any occurrence)     | P2       | Page primary and backup on-call                   |
| LLM schema validation failure rate > 5%    | P2       | Page primary on-call; block new LLM calls         |
| Kill-switch activated                      | P1       | Page primary + engineering lead + DPO             |
| Error budget > 75% consumed                | P3       | Ticket assigned to SRE Lead; feature freeze       |

### 3.7 Recording rules

Pre-computed recording rules reduce query cost for burn rate calculations:

```promql
# 1h error ratio — Critical tier
record: job:slo_c01_error_ratio:rate1h
expr: sum(rate(http_requests_total{service="orchestrator",status_code=~"5.."}[1h]))
      / sum(rate(http_requests_total{service="orchestrator"}[1h]))

# 30-day error budget consumed (%)
record: job:slo_c01_budget_consumed:30d
expr: 1 - (
  sum(rate(http_requests_total{service="orchestrator",status_code!~"5.."}[30d]))
  / sum(rate(http_requests_total{service="orchestrator"}[30d]))
) / 0.001
```

Recording rules are defined in `infrastructure/prometheus/recording-rules.yml`.

---

## 4. Acceptance Criteria

- [ ] Five SLIs defined (SLI-01 to SLI-05) with good event definition for each
- [ ] SLO targets defined for all 3 tiers (Critical, Standard, Internal) with error budget in minutes/hours per 30 days
- [ ] SLO-C03 (audit trail) documented as zero-tolerance
- [ ] Multi-window multi-burn-rate thresholds for Critical tier cover all 4 alert windows (1h, 6h, 24h, 72h)
- [ ] Prometheus alert rule PromQL example provided for P1 burn rate
- [ ] Error budget policy covers 5 consumption bands with actions
- [ ] On-call trigger table covers at minimum: P1/P2 burn rate, audit trail failure, HITL timeout, kill-switch
- [ ] Recording rules section references `infrastructure/prometheus/recording-rules.yml`
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                  |
| -------- | ---------------------------------------------------------- |
| ADR-0011 | Golden Signals — metric names used in SLI measurements     |
| ADR-0015 | SLO-based alerting — multi-window multi-burn-rate strategy |
| ADR-0023 | HITL enforcement — HITL responsiveness SLI-04              |
| ADR-0024 | Immutable audit trail — zero-tolerance SLO-C03             |
| ADR-0025 | Kill-switch — on-call trigger condition                    |

---

## References

- `docs/adr/ADR-0015-slo-based-alerting-thresholds.md`
- `specs/observability/08-golden-signals.md` — metric names and labels used in SLIs
- `specs/system/03-incident-lifecycle.md` — MTTD < 5 min P1 target derives from SLO-C01 burn rate window
- `infrastructure/prometheus/recording-rules.yml` — recording rule definitions (Phase 5)
