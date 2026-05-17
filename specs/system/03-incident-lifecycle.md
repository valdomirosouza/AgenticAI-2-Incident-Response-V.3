# Spec 03: Incident Lifecycle

**Domain**: system
**Owner**: Tech Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #9
**Review cadence**: Every major release or on SLO change

---

## 1. Purpose

Define the end-to-end incident lifecycle that the Copilot supports — from failure
perception through detection, triage, root cause analysis, remediation and post-mortem
— with quantitative MTTD and MTTR acceptance criteria per stage.

---

## 2. Context

The Copilot's primary value proposition is measurable reduction of MTTD and MTTR
(CLAUDE.md §1.1). To measure improvement, each lifecycle stage must have a defined
start time, end time and acceptance threshold. Without these definitions, the
dissertation's RQ1 and RQ2 cannot be answered with quantitative evidence (RULE-002).

The lifecycle is based on the ITIL 4 Incident Management practice and the SRE
post-mortem culture (ADR-0010), adapted for an agentic AI operator.

---

## 3. Decision

### 3.1 Lifecycle stages

```
  T₀           T₁            T₂           T₃           T₄            T₅
  │            │             │            │            │             │
  ▼            ▼             ▼            ▼            ▼             ▼
ONSET ──► DETECTION ──► TRIAGE ──► INVESTIGATION ──► REMEDIATION ──► CLOSED
           │                │              │               │
           │◄──── MTTD ────►│              │               │
           │                │◄─────────────────── MTTR ───►│
```

| Stage             | Start event (Tₙ)                                 | End event (Tₙ₊₁)                           | Owner agent      |
| ----------------- | ------------------------------------------------ | ------------------------------------------ | ---------------- |
| **Onset**         | First anomalous signal in observability data     | —                                          | —                |
| **Detection**     | `incident.created` fired by DetectionAgent       | `incident.severity_set` by TriageAgent     | DetectionAgent   |
| **Triage**        | `incident.severity_set`                          | `rca.hypothesis_set` by RCAAgent           | TriageAgent      |
| **Investigation** | `rca.hypothesis_set`                             | `remediation.proposed` by RemediationAgent | RCAAgent         |
| **Remediation**   | Engineer approves (`PRODUCTION_*` ApprovalToken) | `incident.resolved`                        | RemediationAgent |
| **Post-mortem**   | `incident.resolved`                              | `postmortem.drafted` published             | PostMortemAgent  |

### 3.2 MTTD definition

**MTTD** = T₁ (DetectionAgent fires `incident.created`) − T₀ (first anomalous signal)

T₀ is defined as the timestamp of the first metric sample or log line that crosses the
alert threshold that would eventually trigger the incident, as determined retrospectively
from the observability data.

**Baseline MTTD** (human-only): time from T₀ to when the on-call engineer acknowledges
the PagerDuty alert after manual review.

**Target**: MTTD with Copilot ≤ 80% of baseline MTTD (≥ 20% reduction, objective O1
from spec 00).

**P1 hard threshold**: MTTD < 5 minutes (ADR-0015 SLO).

### 3.3 MTTR definition

**MTTR** = T₄ (`incident.resolved`) − T₁ (`incident.created`)

MTTR encompasses triage + investigation + remediation. Post-mortem is excluded from
MTTR as it occurs after service restoration.

**Baseline MTTR** (human-only): time from T₁ to incident closure in the ticketing system,
measured from historical records in the evaluation corpus.

**Target**: MTTR with Copilot ≤ 80% of baseline MTTR (≥ 20% reduction, objective O2
from spec 00).

### 3.4 Quantitative acceptance criteria per stage

| Stage         | P1 target | P2 target  | P3/P4 target | Measurement source                                               |
| ------------- | --------- | ---------- | ------------ | ---------------------------------------------------------------- |
| Detection     | < 5 min   | < 15 min   | < 60 min     | `incident.created.timestamp − T₀`                                |
| Triage        | < 2 min   | < 5 min    | < 15 min     | `incident.severity_set.timestamp − incident.created.timestamp`   |
| Investigation | < 10 min  | < 20 min   | < 60 min     | `remediation.proposed.timestamp − rca.hypothesis_set.timestamp`  |
| HITL window   | 5 min max | 15 min max | 60 min max   | `approval.timestamp − remediation.proposed.timestamp` (ADR-0023) |
| Remediation   | < 15 min  | < 30 min   | < 120 min    | `incident.resolved.timestamp − approval.timestamp`               |
| Total MTTD    | < 5 min   | < 15 min   | < 60 min     | `incident.created.timestamp − T₀`                                |
| Total MTTR    | < 30 min  | < 60 min   | < 180 min    | `incident.resolved.timestamp − incident.created.timestamp`       |

All timestamps are sourced from the immutable audit trail (ADR-0024) — no manual
timestamp entry is accepted as evidence.

### 3.5 Incident severity classification

| Severity | Definition                                                             | CUJ impact                       | Notification      |
| -------- | ---------------------------------------------------------------------- | -------------------------------- | ----------------- |
| **P1**   | Complete service outage or > 50% error rate on a Critical User Journey | All CUJs degraded or unavailable | Immediate page    |
| **P2**   | Partial outage or latency p99 > 2× SLO threshold on a CUJ              | One or more CUJs degraded        | Page within 5 min |
| **P3**   | Non-critical service degraded; no CUJ impact                           | No CUJ impact                    | Ticket + Slack    |
| **P4**   | Informational anomaly; no service degradation                          | No impact                        | Ticket only       |

TriageAgent classifies severity using Golden Signals thresholds from ADR-0011 and the
SLO breach indicators from ADR-0015. Classification confidence must be ≥ 0.6 (ADR-0021).

### 3.6 Escalation rules

| Condition                                              | Action                                                                    |
| ------------------------------------------------------ | ------------------------------------------------------------------------- |
| HITL approval window expires (P1: 5 min, P2: 15 min)   | OrchestratorAgent escalates to P1; pages backup on-call; NO auto-execute  |
| RCAAgent confidence < 0.6                              | Surface hypothesis with low-confidence label; request human investigation |
| RemediationAgent proposes action with no runbook match | HITL mandatory regardless of severity; flag as UNKNOWN_REMEDIATION        |
| Two consecutive remediation attempts fail              | Escalate to engineering lead; freeze further automation                   |
| DetectionAgent fires duplicate `incident.created`      | OrchestratorAgent deduplicates by correlation window (5 min)              |

### 3.7 Post-mortem obligations

Per ADR-0010, a blameless post-mortem must be drafted within 90 days of incident close
(ADR-0030 retention policy). PostMortemAgent produces a draft covering:

1. Incident summary with MTTD and MTTR figures from audit trail
2. Timeline (T₀ → T₄) reconstructed from audit events
3. Root cause (from RCAAgent hypothesis, human-confirmed)
4. Contributing factors
5. Action items with owner roles (pseudonymised) and due dates
6. What went well / what can be improved

The draft is surfaced for human review (HOTL) before publication. Engineer names are
never used — only role labels (e.g. `engineer_alpha`) per ADR-0010.

### 3.8 Privacy Impact

- All timestamps and incident IDs in the audit trail are pseudonymised role labels —
  no engineer names (ADR-0010, ADR-0024).
- Evaluation corpus MTTD/MTTR measurements are computed on anonymized datasets per
  ADR-0031; timestamps rounded to the nearest minute for k-anonymity compliance.
- Post-mortem drafts are PII-scrubbed before storage (ADR-0028 sanitization applied
  to any text containing observability excerpts).

---

## 4. Acceptance Criteria

- [ ] Lifecycle diagram covers all 6 stages: Onset, Detection, Triage, Investigation, Remediation, Post-mortem
- [ ] MTTD and MTTR are formally defined with start/end events referenced to audit trail event types
- [ ] Quantitative targets defined for P1, P2, P3/P4 for each stage
- [ ] Severity classification table defines P1–P4 with CUJ impact and notification channel
- [ ] Escalation rules cover: HITL timeout, low RCA confidence, unknown remediation, duplicate detection
- [ ] Post-mortem obligations include 90-day deadline and 6 mandatory sections
- [ ] All time measurements reference ADR-0024 audit trail as the authoritative source
- [ ] Privacy Impact section documents pseudonymisation of timestamps and post-mortem scrubbing
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                                   |
| -------- | --------------------------------------------------------------------------- |
| ADR-0004 | Multi-agent orchestration — agent handoff sequence matches lifecycle stages |
| ADR-0010 | Blameless post-mortem format — 8-section structure, role pseudonymisation   |
| ADR-0011 | Golden Signals — severity classification thresholds                         |
| ADR-0015 | SLO-based alerting — MTTD < 5 min P1 hard threshold                         |
| ADR-0021 | OWASP LLM Top 10 — confidence threshold ≥ 0.6 for automated outputs         |
| ADR-0023 | HITL enforcement — approval windows and escalation on timeout               |
| ADR-0024 | Immutable audit trail — authoritative source for all timestamp measurements |
| ADR-0028 | PII sanitization — post-mortem text scrubbing                               |
| ADR-0030 | Data retention — post-mortem 90-day deadline; evaluation corpus TTL         |
| ADR-0031 | Anonymization standard — MTTD/MTTR timestamps in evaluation corpus          |

---

## References

- CLAUDE.md §1.1 Purpose (MTTD/MTTR definitions)
- CLAUDE.md §4.2 Canonical Glossary (MTTD, MTTR, HITL, HOTL, CUJ)
- CLAUDE.md §5 RULE-002 (quantitative evidence requirements)
- `specs/system/00-project-brief.md` — objectives O1 and O2 (≥ 20% reduction targets)
- `specs/system/02-agent-design.md` — agent state machine and action types
- `docs/adr/ADR-0010-blameless-post-mortem-format.md`
- `docs/adr/ADR-0015-slo-based-alerting-thresholds.md`
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md`
