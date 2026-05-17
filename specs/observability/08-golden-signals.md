# Spec 08: Golden Signals

**Domain**: observability
**Owner**: SRE Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #11
**Linked ADRs**: ADR-0011
**Review cadence**: Quarterly or on SLO change

---

## 1. Purpose

Define the canonical Golden Signal metric set (Latency, Error Rate, Traffic, Saturation)
with Prometheus metric names, labelling conventions and p50/p95/p99 targets per service
tier. This is the authoritative source for alert threshold configuration and dashboard
definitions.

---

## 2. Context

The DetectionAgent uses Golden Signal anomalies as the primary trigger for
`incident.created` (spec 03). Without explicit numeric targets per service tier, the
DetectionAgent cannot distinguish noise from a real incident — leading to false positives
that degrade trust, or missed thresholds that increase MTTD.

ADR-0011 selected the four Google SRE Golden Signals as the canonical metric set and
mandated Prometheus naming conventions. This spec operationalises those targets.

---

## 3. Decision

### 3.1 Service tiers

| Tier         | Services                                                                 | Criticality |
| ------------ | ------------------------------------------------------------------------ | ----------- |
| **Critical** | OrchestratorAgent API, HITL approval endpoint                            | P1-capable  |
| **Standard** | DetectionAgent, TriageAgent, RCAAgent, RemediationAgent, PostMortemAgent | P2-capable  |
| **Internal** | Vault sidecar, OTel Collector, Prometheus, Loki, Tempo                   | P3-capable  |

### 3.2 Latency

Metric: `http_request_duration_seconds` (histogram, seconds)

Required labels: `service`, `endpoint`, `method`, `status_code`

| Tier         | p50 target | p95 target | p99 target  | Measurement window |
| ------------ | ---------- | ---------- | ----------- | ------------------ |
| **Critical** | ≤ 200 ms   | ≤ 500 ms   | ≤ 1 000 ms  | 5-minute rolling   |
| **Standard** | ≤ 500 ms   | ≤ 2 000 ms | ≤ 5 000 ms  | 5-minute rolling   |
| **Internal** | ≤ 1 000 ms | ≤ 5 000 ms | ≤ 10 000 ms | 5-minute rolling   |

LLM inference latency (Anthropic API round-trip) is tracked separately:

| Metric                         | p50 target | p95 target  | Alert threshold |
| ------------------------------ | ---------- | ----------- | --------------- |
| `llm_request_duration_seconds` | ≤ 3 000 ms | ≤ 10 000 ms | p95 > 15 000 ms |

LLM latency is informational — it does not trigger incident.created directly but feeds
TriageAgent for MTTD budget estimation.

Prometheus query for p99 alert:

```promql
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket{service="orchestrator"}[5m])) by (le)
) > 1.0
```

### 3.3 Error Rate

Metric: `http_requests_total` (counter)

Required labels: `service`, `endpoint`, `method`, `status_code`

| Tier         | Error rate alert threshold | Severity on breach |
| ------------ | -------------------------- | ------------------ |
| **Critical** | > 1% over 1 minute         | P1                 |
| **Standard** | > 5% over 5 minutes        | P2                 |
| **Internal** | > 10% over 10 minutes      | P3                 |

Error rate calculation:

```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)
/
sum(rate(http_requests_total[5m])) by (service)
```

**LLM-specific error signals** tracked separately:

| Metric                                 | Description                                      | Alert threshold                       |
| -------------------------------------- | ------------------------------------------------ | ------------------------------------- |
| `llm_sanitization_failures_total`      | Prompts blocked by PII gate (ADR-0028)           | > 0 in 5 min (audit event, not error) |
| `llm_schema_validation_failures_total` | Pydantic schema rejections (ADR-0021)            | > 5% response rate                    |
| `hitl_approval_timeouts_total`         | HITL windows expired without approval (ADR-0023) | Any occurrence → P2                   |

### 3.4 Traffic

Metric: `http_requests_total` (counter, same as error rate)

| Tier         | Traffic metric                  | Saturation proxy when traffic drops > 50%                   |
| ------------ | ------------------------------- | ----------------------------------------------------------- |
| **Critical** | Requests/second on orchestrator | `incident.created` volume also drops → check DetectionAgent |
| **Standard** | Agent invocations/second        | Check OTel Collector pipeline                               |
| **Internal** | Scrape targets alive            | Prometheus `up == 0` → P2 alert                             |

Traffic volume is used to distinguish a quiet period (genuine low-traffic) from a silent
failure (pipeline broken). Correlation with `incident.created` rate is a key signal.

### 3.5 Saturation

| Resource         | Metric                                | Tier     | Alert threshold     |
| ---------------- | ------------------------------------- | -------- | ------------------- |
| CPU              | `container_cpu_usage_seconds_total`   | All      | > 80% for 5 min     |
| Memory           | `container_memory_working_set_bytes`  | All      | > 85% of limit      |
| Disk             | `node_filesystem_avail_bytes`         | Internal | < 15% free          |
| LLM token budget | `llm_tokens_used_total` / monthly cap | Critical | > 80% of budget     |
| HITL queue       | `hitl_pending_approvals`              | Critical | > 3 pending → P2    |
| Audit trail      | `audit_trail_write_errors_total`      | Critical | Any occurrence → P1 |

### 3.6 Metric naming conventions

Per ADR-0011 and Prometheus best practices:

```
<namespace>_<subsystem>_<name>_<unit>
```

| Namespace | Used by                    |
| --------- | -------------------------- |
| `http`    | API layer request metrics  |
| `llm`     | LLM adapter metrics        |
| `agent`   | Per-agent decision metrics |
| `hitl`    | HITL approval workflow     |
| `audit`   | Audit trail write metrics  |
| `pii`     | PII sanitization events    |

All metrics must include `service` and `version` labels. No PII in label values
(ADR-0014 enforced at OTel Collector level).

---

## 4. Acceptance Criteria

- [ ] p50/p95/p99 latency targets defined for all 3 service tiers (Critical, Standard, Internal)
- [ ] LLM latency tracked with separate metric `llm_request_duration_seconds`
- [ ] Error rate thresholds defined per tier with severity on breach
- [ ] LLM-specific error signals listed: sanitization failures, schema rejections, HITL timeouts
- [ ] Saturation table covers CPU, memory, disk, LLM token budget, HITL queue, audit trail
- [ ] Prometheus metric naming convention documented with namespace table
- [ ] All label definitions exclude PII (reference ADR-0014)
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                            |
| -------- | -------------------------------------------------------------------- |
| ADR-0011 | Golden Signals canonical metric set — Prometheus naming, 4 signals   |
| ADR-0014 | PII masking — no PII in metric labels                                |
| ADR-0015 | SLO-based alerting — burn rate thresholds derived from these targets |
| ADR-0021 | OWASP LLM Top 10 — schema validation failure metric (LLM05)          |
| ADR-0023 | HITL enforcement — HITL timeout metric                               |
| ADR-0024 | Audit trail — write error metric (Critical tier saturation)          |
| ADR-0028 | PII sanitization — sanitization failure metric                       |

---

## References

- CLAUDE.md §4.2 Canonical Glossary (Golden Signals, MTTD)
- `docs/adr/ADR-0011-golden-signals-canonical-metric-set.md`
- `specs/system/03-incident-lifecycle.md` — MTTD < 5 min P1 target
- `specs/observability/11-slo-definitions.md` — error budget derived from these targets
