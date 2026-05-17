# Skill: Bias and Fairness

**Domain**: ethics
**Activation triggers**: algorithmic bias, fairness audit, bias metrics, Fairlearn, decision auditing, shadow agents, SCER, CV_MTTD, RCRR, KL divergence, data drift, kill-switch drill
**References**: specs/ethics/18-bias-audit-plan.md, ADR-0026

---

## Agents in Scope

| Agent           | Bias risk                                                                       | Primary metric                              |
| --------------- | ------------------------------------------------------------------------------- | ------------------------------------------- |
| **TriageAgent** | Severity miscalibration across service groups                                   | Severity calibration error rate (SCER)      |
| **RCAAgent**    | Root cause over-fitting to historical patterns; data drift from training corpus | Root cause repetition rate (RCRR); KL_drift |

---

## Four Bias Metrics

### Metric 1 — Severity Calibration Error Rate (SCER) — TriageAgent

```
SCER = (incidents where TriageAgent severity ≠ human-validated severity)
       / (total incidents in audit period)
```

| Threshold  | Condition                | Action                                                   |
| ---------- | ------------------------ | -------------------------------------------------------- |
| SCER ≤ 10% | Overall — pass           | No action required                                       |
| SCER > 10% | Overall — fail           | Investigate triage prompt; retrain TriageAgent; re-audit |
| SCER > 15% | Any single service group | Targeted 30-day investigation + prompt engineering fix   |

### Metric 2 — Service-Group MTTD Disparity (CV_MTTD) — TriageAgent

```
CV_MTTD = std(MTTD per service group) / mean(MTTD per service group)
```

Threshold: CV_MTTD ≤ 0.30. CV > 0.30 → some service groups are systematically detected faster or slower than average.

**Tool**: Fairlearn `MetricFrame` — decomposes MTTD by service group without requiring demographic attributes.

```python
from fairlearn.metrics import MetricFrame
import numpy as np

mf = MetricFrame(
    metrics={"mttd_mean": np.mean, "mttd_std": np.std},
    y_true=mttd_baseline,
    y_pred=mttd_measured,
    sensitive_features=service_groups,
)
cv_mttd = mf.by_group["mttd_std"].mean() / mf.by_group["mttd_mean"].mean()
```

### Metric 3 — Root Cause Repetition Rate (RCRR) — RCAAgent

```
RCRR = (incidents where RCAAgent root cause = top-3 most frequent root causes)
       / (total incidents in audit period)
```

Threshold: RCRR ≤ 60%. Higher rate → agent over-fits to common patterns, producing low-quality hypotheses for novel failures.

### Metric 4 — Data Drift Index (KL Divergence) — RCAAgent

```
KL_drift = KL_divergence(P_current_features || P_training_features)
```

Where `P_current_features` = distribution of input features (log anomaly scores, metric values, trace error rates) in the current quarter; `P_training_features` = distribution at training time.

Threshold: KL_drift ≤ 0.10. Above 0.10 → model's training distribution no longer matches production.

```python
from scipy.special import kl_div
import numpy as np

kl_drift = np.sum(kl_div(p_current, p_training))
```

---

## Audit Cadence

| Activity                          | Frequency     | Responsible                 | Deadline relative to release |
| --------------------------------- | ------------- | --------------------------- | ---------------------------- |
| Run bias metrics script           | Quarterly     | Tech Lead                   | ≥ 14 days before release     |
| Review metric results             | Quarterly     | Tech Lead + Ethics reviewer | ≥ 7 days before release      |
| Write audit report                | Quarterly     | Tech Lead                   | ≥ 5 days before release      |
| Store report in `data/audit/`     | Quarterly     | Tech Lead                   | ≥ 5 days before release      |
| Release gate check (report ≤ 90d) | Every release | CI pipeline                 | At release gate (ADR-0026)   |

The CI release gate (`harness/release-check.yml`) blocks if:

- No report exists, or
- Report is older than 90 days, or
- Any metric exceeds its threshold with no documented remediation plan.

---

## Audit Report Schema

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

A report with `release_gate_pass: false` blocks production deployment. If any metric exceeds its threshold, `findings` must contain a structured finding and `remediation_plan` must be non-null.

---

## Remediation Criteria

| Metric          | Threshold exceeded | Required action                                                           | Owner     |
| --------------- | ------------------ | ------------------------------------------------------------------------- | --------- |
| SCER > 10%      | Overall            | Investigate triage prompt; retrain or fine-tune TriageAgent; re-audit     | Tech Lead |
| SCER > 15%      | Any service group  | Targeted review; prompt engineering fix within 30 days                    | Tech Lead |
| CV_MTTD > 0.30  | —                  | Identify outlier service groups; add group-specific context to prompts    | SRE Lead  |
| RCRR > 60%      | —                  | Expand RCA prompt with recent novel failure modes; review training corpus | Tech Lead |
| KL_drift > 0.10 | —                  | Schedule model retraining/fine-tuning; freeze RCAAgent pending retraining | Tech Lead |

Unresolved findings after one quarter are escalated to the Ethics reviewer and recorded in the DPIA/RIPD (spec 21).

---

## Kill-Switch Drill (Quarterly)

Required at the same cadence as the bias audit — both must pass for the release gate:

1. Activate kill-switch via authenticated API endpoint (or automatic trigger)
2. Verify RTO < 60 seconds: all specialist agents terminated + Vault tokens revoked
3. Verify `agent.kill_switch_activated` audit event written
4. Verify audit chain integrity remains valid after the event
5. Document result in the bias audit report (`kill_switch_drill` section)

```json
"kill_switch_drill": {
  "drill_date": "2026-06-15",
  "rto_seconds": 34,
  "rto_pass": true,
  "audit_event_written": true,
  "chain_integrity_pass": true
}
```

---

## Running the Bias Audit Locally

```shell
# Run all four metrics
python src/research/bias_audit.py \
  --period 2026-Q2 \
  --audit-trail-path data/audit/audit-trail-2026-Q2.json \
  --output data/audit/bias-audit-2026-Q2.json

# Review the report
cat data/audit/bias-audit-2026-Q2.json | python -m json.tool

# Validate the report passes the release gate schema
python harness/scripts/check_bias_report.py data/audit/bias-audit-2026-Q2.json
```
