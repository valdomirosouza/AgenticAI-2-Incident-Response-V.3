# Spec 18: Bias Audit Plan

**Domain**: ethics
**Owner**: Tech Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #13
**Linked ADRs**: ADR-0026
**Review cadence**: Semi-annually; Ethics reviewer + Legal required

---

## 1. Purpose

Define the quarterly bias audit cadence, bias metrics, measurement tooling, responsible
parties and remediation criteria for the two agents most likely to exhibit biased
behaviour: TriageAgent and RCAAgent.

---

## 2. Context

ADR-0026 established a quarterly bias audit as a release gate. EU AI Act Art. 10
requires data governance and bias monitoring for high-risk AI systems. IEEE 7000
requires algorithmic impact assessment. Without explicit metrics and thresholds, a
"bias audit" is a checkbox exercise with no power to detect or prevent discriminatory
outcomes.

The Copilot's bias risk is specific: TriageAgent may systematically misclassify
incidents affecting certain service groups (e.g. services owned by smaller teams, legacy
stacks, or non-English-language services) as lower severity than they deserve, leading
to longer MTTD/MTTR for those groups. RCAAgent may over-fit to common root cause
patterns and under-diagnose novel failure modes, disadvantaging teams whose incidents
don't match historical patterns.

---

## 3. Decision

### 3.1 Agents in scope

| Agent           | Bias risk                                                                       | Primary metric                               |
| --------------- | ------------------------------------------------------------------------------- | -------------------------------------------- |
| **TriageAgent** | Severity miscalibration across service groups                                   | Severity calibration error rate              |
| **RCAAgent**    | Root cause over-fitting to historical patterns; data drift from training corpus | Root cause repetition rate; data drift index |

### 3.2 Bias metrics

#### TriageAgent

**Metric 1 — Severity calibration error rate (SCER)**

```
SCER = (number of incidents where TriageAgent severity ≠ human-validated severity)
       / (total incidents in audit period)
```

Threshold: SCER ≤ 10% overall. If SCER for any service group exceeds 15%, that group
triggers a targeted investigation.

**Metric 2 — Service-group MTTD disparity (coefficient of variation)**

```
CV_MTTD = std(MTTD per service group) / mean(MTTD per service group)
```

Threshold: CV_MTTD ≤ 0.30. A CV above 0.30 indicates that some service groups are
systematically detected faster or slower than average — a fairness concern.

#### RCAAgent

**Metric 3 — Root cause repetition rate (RCRR)**

```
RCRR = (number of incidents where RCAAgent root cause = top-3 most frequent root causes)
       / (total incidents in audit period)
```

Threshold: RCRR ≤ 60%. A higher rate suggests the agent over-fits to common patterns
and may be producing low-quality hypotheses for novel failures.

**Metric 4 — Data drift index (KL divergence)**

```
KL_drift = KL_divergence(P_current_features || P_training_features)
```

Where `P_current_features` is the distribution of input features (log anomaly scores,
metric values, trace error rates) in the current quarter and `P_training_features` is
the distribution at training time.

Threshold: KL_drift ≤ 0.10. Above this threshold, the model's training distribution no
longer matches production data — requiring retraining or fine-tuning.

### 3.3 Measurement tooling

| Metric   | Tool                                                | Data source                                              |
| -------- | --------------------------------------------------- | -------------------------------------------------------- |
| SCER     | Custom Python script (`src/research/bias_audit.py`) | Audit trail + human validation labels                    |
| CV_MTTD  | Fairlearn `MetricFrame`                             | Audit trail MTTD measurements per service group          |
| RCRR     | Custom script                                       | Audit trail `rca.hypothesis_set` events                  |
| KL_drift | SciPy `entropy` function                            | Feature distribution snapshots (stored in `data/audit/`) |

Fairlearn `MetricFrame` decomposes MTTD by service group and computes group-level
statistics. It does not require individual-level protected attributes — service group
is a functional label, not a demographic.

All bias audit scripts are in `src/research/bias_audit.py` and produce a structured
JSON report stored in `data/audit/bias-audit-<YYYY-QN>.json`.

### 3.4 Audit cadence and schedule

| Activity                              | Frequency     | Responsible party           | Deadline relative to release |
| ------------------------------------- | ------------- | --------------------------- | ---------------------------- |
| Run bias metrics script               | Quarterly     | Tech Lead                   | ≥ 14 days before release     |
| Review metric results                 | Quarterly     | Tech Lead + Ethics reviewer | ≥ 7 days before release      |
| Write audit report                    | Quarterly     | Tech Lead                   | ≥ 5 days before release      |
| Store report in `data/audit/`         | Quarterly     | Tech Lead                   | ≥ 5 days before release      |
| Release gate check (report ≤ 90 days) | Every release | CI pipeline (ADR-0026)      | At release gate              |

The CI release gate (`harness/release-check.yml`) reads the most recent
`data/audit/bias-audit-*.json` and blocks the release if:

- No report exists, or
- The report is older than 90 days, or
- Any metric exceeds its threshold with no documented remediation plan.

### 3.5 Audit report structure

Each quarterly report (`data/audit/bias-audit-<YYYY-QN>.json`) must contain:

```json
{
  "period": "2026-Q2",
  "audit_date": "2026-06-15",
  "auditor": "Tech Lead",
  "triage_agent": {
    "scer": 0.08,
    "scer_threshold": 0.1,
    "scer_pass": true,
    "cv_mttd": 0.22,
    "cv_mttd_threshold": 0.3,
    "cv_mttd_pass": true,
    "service_group_breakdown": {
      "payments": 0.07,
      "auth": 0.09,
      "legacy_api": 0.13
    }
  },
  "rca_agent": {
    "rcrr": 0.52,
    "rcrr_threshold": 0.6,
    "rcrr_pass": true,
    "kl_drift": 0.07,
    "kl_drift_threshold": 0.1,
    "kl_drift_pass": true
  },
  "findings": [],
  "remediation_plan": null,
  "release_gate_pass": true
}
```

If any metric fails its threshold, `findings` must contain a structured finding with
severity, description and proposed remediation, and `remediation_plan` must be non-null.

### 3.6 Remediation criteria

| Metric          | Threshold exceeded | Required action                                                                            | Owner     |
| --------------- | ------------------ | ------------------------------------------------------------------------------------------ | --------- |
| SCER > 10%      | Overall            | Investigate triage prompt; retrain or fine-tune TriageAgent; re-audit                      | Tech Lead |
| SCER > 15%      | Any service group  | Targeted review of that group's incidents; prompt engineering fix within 30 days           | Tech Lead |
| CV_MTTD > 0.30  | —                  | Identify which service groups are outliers; add group-specific context to prompts          | SRE Lead  |
| RCRR > 60%      | —                  | Expand RCA prompt with recent novel failure modes; review training corpus                  | Tech Lead |
| KL_drift > 0.10 | —                  | Schedule model retraining/fine-tuning; freeze new incidents to RCAAgent pending retraining | Tech Lead |

A remediation plan must be documented in the audit report and completed before the next
quarterly audit. If not resolved within one quarter, the finding is escalated to the
Ethics reviewer and recorded in the DPIA/RIPD (ADR-0029).

### 3.7 Kill-switch drill

Per ADR-0025, a kill-switch drill is required quarterly (same cadence as the bias
audit). The drill verifies that:

1. The kill-switch activation path works end-to-end (pod termination + Vault revocation).
2. RTO < 60 seconds is achieved.
3. An `agent.kill_switch_activated` audit event is written and the chain remains valid.

The drill result is documented alongside the bias audit report. Both are required for
the release gate.

### 3.8 Privacy Impact

- Bias audit data is sourced from the anonymized evaluation corpus (ADR-0031) and the
  audit trail (ADR-0024). No raw PII is accessed during audits.
- Service group labels used in Fairlearn MetricFrame are functional labels (service
  names), not demographic or personal attributes — no LGPD/GDPR special category data.
- Audit reports are stored in `data/audit/` with no PII content and are not subject
  to data retention TTL limits (they are compliance records, similar to DPIA/RIPD).

---

## 4. Acceptance Criteria

- [ ] Both agents (TriageAgent, RCAAgent) are in scope with documented bias risk
- [ ] Four bias metrics defined: SCER, CV_MTTD (TriageAgent); RCRR, KL_drift (RCAAgent)
- [ ] Each metric has a numeric threshold and a formula
- [ ] Measurement tooling names Fairlearn MetricFrame for CV_MTTD; SciPy entropy for KL_drift
- [ ] Audit report JSON structure defined with all required fields including `release_gate_pass`
- [ ] Remediation criteria table covers all 5 threshold breach scenarios with owner
- [ ] Kill-switch drill documented at quarterly cadence alongside bias audit
- [ ] Privacy Impact confirms no PII in audit data sources
- [ ] Ethics reviewer + Legal review recorded before merge
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                               |
| -------- | ----------------------------------------------------------------------- |
| ADR-0024 | Immutable audit trail — source of `rca.hypothesis_set` and MTTD events  |
| ADR-0025 | Kill-switch — quarterly drill cadence tied to bias audit                |
| ADR-0026 | Algorithmic bias audit — quarterly cadence, release gate, metric scope  |
| ADR-0029 | DPIA/RIPD — unresolved findings escalated to impact assessment          |
| ADR-0031 | Anonymization standard — bias audit data sourced from anonymized corpus |

---

## References

- EU AI Act (2024) Art. 10 — Data governance and bias monitoring
- IEEE 7000 — Model process for addressing ethical concerns during system design
- NIST AI RMF GOVERN-5 — Organizational risk tolerance
- Microsoft Fairlearn — fairlearn.org
- `docs/adr/ADR-0026-algorithmic-bias-audit-cadence.md`
- `src/research/bias_audit.py` — audit script (Phase 5)
- `data/audit/` — quarterly audit reports
