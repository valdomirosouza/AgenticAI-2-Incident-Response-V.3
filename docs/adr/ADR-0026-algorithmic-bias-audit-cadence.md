# ADR-0026: Algorithmic Bias Audit — Quarterly Review by Service Group

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Ethics Reviewer — researcher)
**Affected RQs**: RQ2 (MTTD/MTTR quality), RQ4 (compliance, fairness)

---

## Context

The Copilot's agents — particularly TriageAgent (severity scoring) and RCAAgent
(hypothesis generation) — make decisions that directly affect which incidents are
prioritised and how quickly they are resolved. If these agents exhibit systematic
bias, certain services, teams or incident types may receive systematically slower
or lower-quality responses, undermining both the dissertation's quantitative claims
and the ethical foundations of the system.

Bias in AI incident response systems can manifest as:

1. **Service-group bias**: certain services (historically under-instrumented or
   recently onboarded) may be systematically under-triaged because the LLM's
   training data underrepresents them.
2. **Severity inflation/deflation**: the TriageAgent may consistently over- or
   under-score certain incident types, distorting MTTD measurement.
3. **RCA pattern anchoring**: the RCAAgent may over-rely on the most common root
   cause patterns in the training corpus, missing novel failure modes (OWASP LLM09).
4. **Temporal bias**: agent performance may degrade over time as the production
   environment evolves away from the evaluation corpus (data drift).

Two frameworks mandate bias assessment for AI systems:

- **EU AI Act Art. 10** (Data and data governance): training, validation and testing
  data must be examined for bias that could lead to discriminatory outcomes or
  failures to detect certain risks.
- **IEEE 7000** (Model process for addressing ethical concerns) requires systematic
  identification and mitigation of value conflicts including fairness and equity in
  automated decision-making systems.

## Decision

A **quarterly algorithmic bias audit** is mandatory for the TriageAgent and RCAAgent.
The audit assesses bias across service groups, incident types and time periods.

### Audit scope and metrics

#### TriageAgent bias metrics

| Metric                                   | Definition                                                                               | Bias signal                                                       |
| ---------------------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Severity calibration error**           | Mean absolute difference between TriageAgent severity and post-mortem confirmed severity | > 0.5 severity levels → miscalibration                            |
| **Service-group MTTD disparity**         | Coefficient of variation of MTTD across service groups with similar incident rates       | CV > 0.3 → potential service-group bias                           |
| **False negative rate by incident type** | Fraction of P1 incidents initially scored P2 or below, by incident category              | > 10% in any category → bias toward that type                     |
| **Confidence score distribution**        | Histogram of triage confidence scores by service group                                   | Systematic low confidence for specific groups → training data gap |

#### RCAAgent bias metrics

| Metric                                          | Definition                                                                             | Bias signal                                |
| ----------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------ |
| **Root cause repetition rate**                  | Fraction of RCA hypotheses that cite the top-3 most common root causes                 | > 60% → pattern anchoring                  |
| **Novel incident hypothesis quality**           | Human-scored quality of RCA hypotheses for incident types not in training corpus       | Mean score < 3/5 → generalisation failure  |
| **Hypothesis acceptance rate by service group** | Fraction of RCA hypotheses accepted by incident commander per service group            | > 20% disparity → possible bias            |
| **Data drift index**                            | KL divergence between current incident distribution and evaluation corpus distribution | > 0.2 → corpus is no longer representative |

### Audit cadence and responsible role

| Cadence                          | Scope                                                             | Responsible role                | Deliverable                               |
| -------------------------------- | ----------------------------------------------------------------- | ------------------------------- | ----------------------------------------- |
| **Quarterly**                    | All metrics above for preceding quarter                           | Ethics Reviewer (researcher)    | `docs/bias-audits/YYYY-QN-bias-report.md` |
| **On model update**              | Full re-audit triggered by LLM provider version change (ADR-0003) | Ethics Reviewer                 | Ad hoc report                             |
| **On significant corpus change** | Re-audit when > 20% new incidents added to evaluation corpus      | Ethics Reviewer                 | Ad hoc report                             |
| **Kill-switch drill**            | Verify kill-switch RTO (ADR-0025)                                 | Ethics Reviewer + Security Lead | Drill log entry                           |

### Audit report structure

Each quarterly report documents:

1. **Summary**: pass/fail for each metric with trend vs. prior quarter.
2. **Findings**: any metric exceeding the bias signal threshold.
3. **Root cause analysis**: systematic cause of any detected bias.
4. **Remediation actions**: concrete steps (retraining, prompt engineering,
   corpus expansion, model change) with owner and due date.
5. **Kill-switch drill result**: RTO achieved, findings, corrective actions.

Reports are stored in `docs/bias-audits/` and reviewed before any production
deployment. A report with open High findings blocks the release gate.

### Bias thresholds as release gate

The release gate (`harness/release-check.yml`) includes a bias gate:

- If the most recent bias audit is > 90 days old → block release.
- If any metric exceeds its bias signal threshold and no remediation action is open → block release.
- If the kill-switch drill has not been run in the current quarter → warn (non-blocking
  until the first production release).

## Alternatives Considered

| Alternative                         | Pros                                                                                                                    | Cons                                                                                                                                                          |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **No bias audit**                   | Zero overhead                                                                                                           | EU AI Act Art. 10 violated; silent service-group disparities in MTTD; dissertation validity undermined                                                        |
| **One-time pre-production audit**   | Low ongoing cost                                                                                                        | Does not detect temporal drift; fails to catch post-deployment degradation                                                                                    |
| **Continuous real-time monitoring** | Earliest detection                                                                                                      | High engineering cost; real-time bias metrics require complex streaming pipelines — disproportionate for a research prototype                                 |
| **Quarterly structured audit** ✅   | Proportionate effort; structured evidence for dissertation; EU AI Act compliant; cadence matches model update frequency | Quarterly lag means bias present for up to 3 months before detection — mitigated by continuous MTTD/MTTR monitoring which surfaces disparity symptoms earlier |

## Consequences

**Positive:**

- EU AI Act Art. 10 satisfied: systematic bias assessment with documented metrics,
  cadence and responsible role.
- Dissertation validity protected: service-group MTTD disparity detected and corrected
  before evaluation results are reported (RULE-003: no toy examples).
- Kill-switch drill embedded in audit cadence — ADR-0025 RTO target is verified
  quarterly, not only at implementation time.
- Bias audit reports are public artifacts in `docs/bias-audits/` — available to
  dissertation examiners and future researchers.

**Negative / Trade-offs:**

- Quarterly audit requires ~4 hours of researcher time per quarter — budgeted in
  the dissertation timeline.
- Bias metrics require structured incident data to compute — depend on the evaluation
  corpus being sufficiently populated (minimum 50 labelled incidents per service group
  for statistical significance).

## Review Criteria

Revisit this decision if:

- The quarterly cadence misses a critical bias event between audits — shorten to
  monthly for the period immediately following an LLM model change.
- The bias signal thresholds produce too many false positives (> 30% of audits flag
  a metric that resolves without intervention) — recalibrate thresholds based on
  accumulated audit history.

## References

- EU AI Act (2024) Art. 10 — Data and data governance
- IEEE Std 7000-2021 — Model process for addressing ethical concerns
- NIST AI RMF (2023) MAP-5 — Likelihood of impact on individuals and groups
- `docs/adr/ADR-0003-llm-provider-model-selection.md` — model version triggers re-audit
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md` — audit trail provides bias metric input data
- `docs/adr/ADR-0025-kill-switch-credential-revocation.md` — kill-switch drill in quarterly audit
- `specs/ethics/18-bias-audit-plan.md` — bias audit plan spec (to be authored, issue #13)
- CLAUDE.md §1.6 criteria 1 and 6 — quantitative evidence + HITL controls
