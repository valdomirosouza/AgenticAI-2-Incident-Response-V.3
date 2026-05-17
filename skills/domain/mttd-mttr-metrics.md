# Skill: MTTD / MTTR Metrics

**Domain**: domain
**Activation triggers**: MTTD, MTTR, mean time to detect, mean time to recover, incident metrics, IR efficiency, AIOps benchmarks
**References**: specs/system/03-incident-lifecycle.md, ADR-0011, ADR-0015, CLAUDE.md §4.2

---

## Canonical Definitions

| Metric   | Definition                                                                          | Start event                      | End event                    |
| -------- | ----------------------------------------------------------------------------------- | -------------------------------- | ---------------------------- |
| **MTTD** | Mean Time to Detect — average time between incident onset and detection             | T₀: first anomalous signal       | T₁: `incident.created` fired |
| **MTTR** | Mean Time to Recovery — average time between detection and full service restoration | T₁: `incident.created`           | T₄: `incident.resolved`      |
| **MTTI** | Mean Time to Investigate — triage + RCA duration                                    | T₁: `incident.created`           | T₃: `remediation.proposed`   |
| **MTTF** | Mean Time to Fix — remediation execution only                                       | T_approve: ApprovalToken granted | T₄: `incident.resolved`      |

> RULE-002: Every quantitative claim about MTTD/MTTR improvement must cite a
> bibliographic source in ABNT format. Never present a target or benchmark without
> a citation.

---

## Formulas

### MTTD (per incident)

```
MTTD_i = T₁_i − T₀_i

where:
  T₁ = timestamp of audit event incident.created
  T₀ = timestamp of first metric sample crossing the detection threshold
       (retrieved retrospectively from Prometheus)
```

### MTTR (per incident)

```
MTTR_i = T₄_i − T₁_i

where:
  T₄ = timestamp of audit event incident.resolved
  T₁ = timestamp of audit event incident.created
```

### Mean over a corpus of N incidents

```
MTTD = (1/N) Σ MTTD_i       (arithmetic mean)
MTTR = (1/N) Σ MTTR_i

Median and p95 are more robust for skewed distributions:
  MTTD_p50 = median(MTTD_i)
  MTTR_p95 = 95th percentile(MTTR_i)
```

### Improvement ratio (Copilot vs. baseline)

```
MTTD_improvement = (MTTD_baseline − MTTD_copilot) / MTTD_baseline × 100%
MTTR_improvement = (MTTR_baseline − MTTR_copilot) / MTTR_baseline × 100%
```

Target: ≥ 20% reduction on both metrics (spec 00, objectives O1 and O2).

---

## Industry Benchmarks

> All benchmarks below are cited in ABNT format per RULE-002. Use only for
> contextualisation — never as direct evidence for this system's performance
> (RULE-003: real evidence required).

**MTTD benchmarks:**

- Mean MTTD across cloud-native organisations: **~197 hours** (IBM Security, 2023)
  — IBM Corporation. _Cost of a Data Breach Report 2023_. Armonk: IBM Security, 2023.
  [This figure covers security breaches; operational MTTD for availability incidents
  is typically much lower — distinguish contexts carefully.]

- P1 incident MTTD target in mature SRE organisations: **< 5 minutes**
  — Beyer, B. et al. _Site Reliability Engineering: How Google Runs Production Systems_.
  Sebastopol: O'Reilly Media, 2016. Chapter 14.

- AIOps-assisted MTTD reduction: **30–50%** reported across surveyed organisations
  — Dang, Y. et al. "AIOps: Real-World Challenges and Research Innovations."
  _IEEE Software_, v. 36, n. 2, p. 182–191, 2019. DOI: 10.1109/MS.2019.2904943.

**MTTR benchmarks:**

- Elite DORA performers MTTR: **< 1 hour**
  — Forsgren, N.; Humble, J.; Kim, G. _Accelerate: The Science of Lean Software and
  DevOps_. Portland: IT Revolution Press, 2018. p. 14.

- High performers MTTR: **< 1 day**
  — Google LLC. _DORA State of DevOps Report 2023_. Mountain View: Google, 2023.

- AIOps-assisted MTTR reduction: **20–40%** over human-only baselines
  — Notaro, P.; Cardoso, J.; Gerndt, M. "A Survey of AIOps Methods for Failure
  Management." _ACM Transactions on Intelligent Systems and Technology_, v. 12, n. 6,
  p. 1–45, 2021. DOI: 10.1145/3483424.

---

## Measurement Instrumentation

### Data sources

| Signal              | Source                                            | Precision                      |
| ------------------- | ------------------------------------------------- | ------------------------------ |
| T₀ (onset)          | Prometheus metric sample crossing alert threshold | ±scrape interval (15s default) |
| T₁ (detection)      | Audit trail `incident.created.timestamp`          | Millisecond (UTC)              |
| T₂ (severity set)   | Audit trail `incident.severity_set.timestamp`     | Millisecond                    |
| T₃ (RCA / proposal) | Audit trail `remediation.proposed.timestamp`      | Millisecond                    |
| T_approve           | Audit trail `remediation.approved.timestamp`      | Millisecond                    |
| T₄ (resolved)       | Audit trail `incident.resolved.timestamp`         | Millisecond                    |

### Prometheus recording rules

```promql
# MTTD per incident (seconds) — computed at detection time
record: incident:mttd_seconds
expr: (
  timestamp(audit_event_timestamp{event="incident.created"})
  - timestamp(audit_event_timestamp{event="first_anomaly_sample"})
)

# MTTR per incident (seconds) — computed at resolution time
record: incident:mttr_seconds
expr: (
  timestamp(audit_event_timestamp{event="incident.resolved"})
  - timestamp(audit_event_timestamp{event="incident.created"})
)

# Rolling 30-day mean MTTD (seconds)
record: incident:mttd_mean_30d
expr: avg_over_time(incident:mttd_seconds[30d])

# Rolling 30-day mean MTTR (seconds)
record: incident:mttr_mean_30d
expr: avg_over_time(incident:mttr_seconds[30d])
```

### Research corpus measurement

For dissertation evaluation (RQ1 and RQ2), MTTD/MTTR are computed from the
anonymised incident corpus (spec 22, ADR-0031) using:

```python
# src/research/compute_mttd_mttr.py
import pandas as pd

def compute_mttd(df: pd.DataFrame) -> pd.Series:
    """RQ1: MTTD per incident. Timestamps rounded to minute for k-anonymity."""
    return (df["t1_detection"] - df["t0_onset"]).dt.total_seconds() / 60  # minutes

def compute_mttr(df: pd.DataFrame) -> pd.Series:
    """RQ2: MTTR per incident."""
    return (df["t4_resolved"] - df["t1_detection"]).dt.total_seconds() / 60  # minutes

def improvement_ratio(baseline: pd.Series, copilot: pd.Series) -> float:
    """(baseline_mean - copilot_mean) / baseline_mean — positive = improvement."""
    return (baseline.mean() - copilot.mean()) / baseline.mean()
```

All timestamps in the corpus are rounded to the nearest minute for k-anonymity
compliance (ADR-0031) — this introduces a ±30s measurement error, acceptable for
the ≥ 20% improvement target.

---

## Statistical Considerations

| Concern                          | Mitigation                                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------------------- |
| Small sample size                | Report confidence intervals (95% CI) alongside means; use non-parametric tests (Mann-Whitney U) |
| Outlier P1 incidents             | Report median and p95 alongside mean; flag outliers in corpus                                   |
| Selection bias in baseline       | Baseline must come from same service group and time period as Copilot evaluation                |
| Timestamp rounding (k-anonymity) | ±30s error; negligible vs. target improvement of minutes                                        |
| Severity mix differences         | Stratify by severity (P1, P2, P3) before computing overall mean                                 |

RULE-003: Always distinguish whether MTTD/MTTR values come from real empirical
evaluation on the anonymised corpus or from a controlled proof-of-concept scenario.
Never present PoC numbers as production evidence.

---

## Quick Reference: This Project's Targets

| Metric           | P1 target | P2 target | Research goal                        |
| ---------------- | --------- | --------- | ------------------------------------ |
| MTTD             | < 5 min   | < 15 min  | ≥ 20% reduction vs. baseline (O1)    |
| MTTR             | < 30 min  | < 60 min  | ≥ 20% reduction vs. baseline (O2)    |
| MTTD improvement | ≥ 20%     | ≥ 20%     | Statistically significant (p < 0.05) |
| MTTR improvement | ≥ 20%     | ≥ 20%     | Statistically significant (p < 0.05) |
