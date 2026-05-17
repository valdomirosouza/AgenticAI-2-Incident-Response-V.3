# ADR-0015: SLO-Based Alerting Thresholds

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (observability architecture), RQ2 (MTTD reduction)

---

## Context

The DetectionAgent must determine when a service health degradation constitutes an
incident worth alerting on. Two failure modes of alerting design directly impact MTTD:

1. **Fixed-value thresholds** (e.g. "alert if p99 latency > 500ms") fire too early
   for bursty services and too late for normally-fast services. They produce high
   false-positive rates, contributing to alert fatigue and degrading MTTD by training
   on-call engineers to ignore alerts.
2. **No alerting strategy** — MTTD is unbounded; incidents are detected by users,
   not the system.

The SRE error budget model (Google SRE Book) solves this by anchoring alert thresholds
to the rate at which the error budget is being consumed — **burn rate** — rather than
to fixed metric values. This approach:

- Fires alerts early enough to matter (fast burn = budget consumed in hours).
- Avoids firing on transient spikes that do not threaten the monthly SLO.
- Self-adjusts as traffic patterns change — no threshold tuning required.
- Directly maps to business impact: a burn rate that exhausts the 30-day budget in
  1 hour is always a P1, regardless of the absolute metric value.

## Decision

All alerting in this project uses **SLO-based alerting with multi-window multi-burn-rate**
rules. Fixed-value metric thresholds are prohibited as primary alert conditions.

### SLO baseline

| Service tier                                | SLO target         | 30-day error budget | Measurement window |
| ------------------------------------------- | ------------------ | ------------------- | ------------------ |
| **Critical** (OrchestratorAgent, HITL gate) | 99.9% availability | 43.8 min/month      | Rolling 30 days    |
| **High** (DetectionAgent, TriageAgent, API) | 99.5% availability | 3.6 hr/month        | Rolling 30 days    |
| **Standard** (PostMortemAgent, RCAAgent)    | 99.0% availability | 7.2 hr/month        | Rolling 30 days    |

SLO targets are defined per service in `specs/observability/11-slo-definitions.md`
(to be authored, issue #11). The values above are the baseline; each service spec
may set a tighter SLO.

### Multi-window multi-burn-rate alert rules

Two alert tiers per SLO, following the Google SRE Workbook recommendation:

#### Tier 1 — Page (P1/P2): fast burn, short window

| Condition                    | Burn rate | Short window | Long window | Severity      |
| ---------------------------- | --------- | ------------ | ----------- | ------------- |
| Budget consumed in < 1 hour  | 14.4×     | 5 min        | 1 hour      | **P1 — Page** |
| Budget consumed in < 6 hours | 6×        | 30 min       | 6 hours     | **P2 — Page** |

**Action:** fires PagerDuty/OpsGenie alert + triggers DetectionAgent incident creation.

#### Tier 2 — Ticket (P3): slow burn, long window

| Condition                   | Burn rate | Short window | Long window | Severity        |
| --------------------------- | --------- | ------------ | ----------- | --------------- |
| Budget consumed in < 3 days | 3×        | 2 hours      | 24 hours    | **P3 — Ticket** |

**Action:** creates a GitHub issue / ticket; no page.

### Alert evaluation

- Detection interval: **30 seconds** (Prometheus scrape interval).
- Multi-window condition: **both** the short and long window must exceed the burn rate
  threshold simultaneously to fire — reduces false positives from transient spikes.
- Alert resolution: automatic when burn rate drops below threshold for two consecutive
  evaluation windows.

### Prohibited alert patterns

- Fixed absolute thresholds as **primary** alert conditions (e.g. `latency > 500ms`).
- Alerts with no SLO backing — every alert must trace to a defined SLO.
- Single-window alerts — multi-window is mandatory to reduce flapping.

Fixed thresholds **may** be used as **secondary** conditions (e.g. `p99 > 2s AND
burn_rate > 6x`) to add human-readable context to the alert message.

### MTTD measurement

MTTD is the elapsed time from SLO burn rate crossing the P1/P2 threshold to the
DetectionAgent firing the incident alert. Target: < 5 minutes for P1 (fast burn at
14.4×). Measured and recorded in every post-mortem (ADR-0010).

## Alternatives Considered

| Alternative                           | Pros                                                                                                | Cons                                                                                                                                      |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Fixed-value thresholds**            | Simple to configure                                                                                 | High false-positive rate; alert fatigue; threshold tuning required per service; does not reflect error budget impact                      |
| **Anomaly detection (ML-based)**      | Self-calibrating; no manual thresholds                                                              | Requires historical training data not yet available; alert rationale opaque (OWASP LLM09 overreliance risk)                               |
| **SLO-based single-window burn rate** | Simpler than multi-window                                                                           | High flapping rate on transient spikes                                                                                                    |
| **Multi-window multi-burn-rate** ✅   | Low false-positive rate; self-adjusting; directly tied to business impact; established SRE practice | Higher configuration complexity; requires Prometheus recording rules — mitigated by `specs/observability/11-slo-definitions.md` templates |

## Consequences

**Positive:**

- Alert fatigue reduced: alerts fire only when the error budget is at risk, not on
  every transient spike. Directly supports MTTD improvement (signal-to-noise ratio).
- Self-adjusting: no threshold tuning required as traffic patterns change.
- Every alert traces to a defined SLO — satisfies ISO 20000-1 service monitoring
  documentation requirement.
- MTTD < 5 minutes for P1 incidents (fast burn 14.4×) — measurable dissertation
  target (RULE-002: quantitative evidence required, RULE-003: no toy examples).

**Negative / Trade-offs:**

- Multi-window burn rate rules require Prometheus recording rules and alerting YAML —
  more complex than a single threshold alert. Templates provided in the observability spec.
- P3 (slow burn) alerts have longer detection time by design (3 days budget horizon) —
  acceptable because P3 incidents do not require immediate human response.
- SLO definitions must be authored before alerting rules can be configured — hard
  dependency on `specs/observability/11-slo-definitions.md` (issue #11).

## Review Criteria

Revisit this decision if:

- False-positive rate for Tier 1 alerts exceeds 10% over a 30-day evaluation window —
  tune burn rate multipliers.
- MTTD target (< 5 min for P1) is not achieved in evaluation experiments — investigate
  whether the burn rate threshold or the evaluation window is too conservative.
- A service with no request-based traffic (e.g. background job) requires a different
  SLO model — define a custom SLO type for non-request services.

## References

- Beyer, B. et al. (2018). _The Site Reliability Workbook_. O'Reilly. Chapter 5 — Alerting on SLOs.
- Beyer, B. et al. (2016). _Site Reliability Engineering_. O'Reilly. Chapter 6 — Monitoring Distributed Systems.
- `docs/adr/ADR-0011-golden-signals-canonical-metric-set.md` — signals used as SLIs
- `docs/adr/ADR-0010-blameless-post-mortem-format.md` — MTTD recorded in post-mortem header
- `specs/observability/08-golden-signals.md` — signal instrumentation
- `specs/observability/11-slo-definitions.md` — per-service SLO definitions (to be authored, issue #11)
- CLAUDE.md §1.6 criterion 1 — quantitative MTTD/MTTR evidence required
