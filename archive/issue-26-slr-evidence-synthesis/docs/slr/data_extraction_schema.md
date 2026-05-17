# SLR Data Extraction Schema

> **Spec reference:** `specs/research/slr-evidence-synthesis.md`
> **Rules:** RULE-R01, RULE-R02, RULE-R03, RULE-C01, RULE-C02
> **Last updated:** 2026-05-17 | Reviewer: Valdomiro de Oliveira Souza Júnior

This document defines the fields extracted per paper during the SLR eligibility
and data extraction phases. Every field maps to at least one research question
(RQ1–RQ4) or a QA rubric criterion (QA1–QA4).

---

## Mandatory Extraction Fields

| Field ID | Field Name           | Type          | Extracted for | Notes                                       |
| -------- | -------------------- | ------------- | ------------- | ------------------------------------------- |
| `DE-01`  | Paper ID             | `string`      | All RQs       | Canonical ID: P01–P19                       |
| `DE-02`  | Full citation (ABNT) | `string`      | All RQs       | RULE-002                                    |
| `DE-03`  | Publication year     | `integer`     | Eligibility   | RULE-R02: 2020–2026 (pre-2020 by exception) |
| `DE-04`  | Venue name           | `string`      | Eligibility   | Conference or journal full name             |
| `DE-05`  | SJR quartile         | `enum`        | Eligibility   | Q1/Q2/Q3/Q4 (RULE-R03)                      |
| `DE-06`  | Qualis stratum       | `enum`        | Eligibility   | A1/A2/B1–B4/C (RULE-R03)                    |
| `DE-07`  | Citation count       | `integer`     | Eligibility   | At time of assessment (RULE-R03: ≥ 1)       |
| `DE-08`  | RQs addressed        | `set[string]` | All           | `{RQ1, RQ2, RQ3, RQ4}` subset               |

---

## QA Rubric Fields (QA1–QA4)

Each criterion scored 0 (NO) / 0.5 (PARTIAL) / 1.0 (YES).
Threshold ≥ 1.5 total → paper qualifies for quantitative claims (RULE-004).

| QA Criterion                               | Field                     | Scoring guide                                                                                                |
| ------------------------------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **QA1** — Quantitative MTTD/MTTR           | `qa1_mttd_mttr`           | YES: explicit values reported; PARTIAL: inferred from related metric; NO: not reported                       |
| **QA2** — Autonomous/agentic component     | `qa2_autonomous`          | YES: autonomous decision cycle; PARTIAL: rule-based automation; NO: detection/alerting only                  |
| **QA3** — Real/realistic dataset           | `qa3_realistic_data`      | YES: production data; PARTIAL: production-derived synthetic; NO: toy or academic benchmark                   |
| **QA4** — Quantitative baseline comparison | `qa4_baseline_comparison` | YES: explicit baseline with delta; PARTIAL: referenced improvement without baseline delta; NO: no comparison |

---

## RQ-Specific Fields

### RQ1 — MTTD Reduction

| Field ID | Field                   | Notes                                                                         |
| -------- | ----------------------- | ----------------------------------------------------------------------------- |
| `RQ1-01` | `mttd_baseline_seconds` | MTTD before AI/agentic intervention                                           |
| `RQ1-02` | `mttd_with_ai_seconds`  | MTTD with AI system active                                                    |
| `RQ1-03` | `mttd_reduction_pct`    | `(baseline − with_ai) / baseline × 100`                                       |
| `RQ1-04` | `mttd_inference_method` | `"direct"`, `"inferred"`, or `"estimated"`                                    |
| `RQ1-05` | `detection_mechanism`   | `"anomaly_detection"`, `"log_analysis"`, `"trace_analysis"`, `"multi-signal"` |

### RQ2 — MTTR Reduction

| Field ID | Field                   | Notes                                                             |
| -------- | ----------------------- | ----------------------------------------------------------------- |
| `RQ2-01` | `mttr_baseline_seconds` | MTTR before AI/agentic intervention                               |
| `RQ2-02` | `mttr_with_ai_seconds`  | MTTR with AI system active                                        |
| `RQ2-03` | `mttr_reduction_pct`    | `(baseline − with_ai) / baseline × 100`                           |
| `RQ2-04` | `mttr_inference_method` | `"direct"`, `"inferred"`, or `"estimated"`                        |
| `RQ2-05` | `remediation_autonomy`  | `"HITL"`, `"HOTL"`, `"fully_autonomous"`, `"recommendation_only"` |
| `RQ2-06` | `remediation_mechanism` | `"RL"`, `"LLM"`, `"rule_based"`, `"multi-agent"`, `"other"`       |

### RQ3 — Bias and Fairness

| Field ID | Field                  | Notes                                                              |
| -------- | ---------------------- | ------------------------------------------------------------------ |
| `RQ3-01` | `bias_metric_used`     | e.g., `"SCER"`, `"CV_MTTD"`, `"RCRR"`, `"demographic_parity"`      |
| `RQ3-02` | `bias_metric_value`    | Numeric value reported                                             |
| `RQ3-03` | `bias_threshold`       | Threshold used to determine pass/fail                              |
| `RQ3-04` | `protected_attributes` | Attributes tested (e.g., `"service_class"`, `"datacenter_region"`) |
| `RQ3-05` | `mitigation_applied`   | Boolean — was a mitigation technique applied?                      |

### RQ4 — Governance Controls

| Field ID | Field                   | Notes                                                                |
| -------- | ----------------------- | -------------------------------------------------------------------- |
| `RQ4-01` | `governance_mechanism`  | `"HITL"`, `"kill_switch"`, `"audit_trail"`, `"XAI"`, `"override"`    |
| `RQ4-02` | `rto_seconds`           | Recovery Time Objective for override activation (if measured)        |
| `RQ4-03` | `compliance_standard`   | Referenced standard (`"EU_AI_Act"`, `"NIST_AI_RMF"`, `"SOC2"`, etc.) |
| `RQ4-04` | `audit_trail_type`      | `"append_only"`, `"hash_chained"`, `"WORM"`, `"none"`                |
| `RQ4-05` | `explainability_method` | `"SHAP"`, `"LIME"`, `"attention"`, `"confidence_score"`, `"none"`    |

---

## Per-Paper Extraction Summary (P01–P19)

| Paper                    | QA Total | Tier         | RQ1 MTTD↓      | RQ2 MTTR↓ | RQ3          | RQ4         |
| ------------------------ | -------- | ------------ | -------------- | --------- | ------------ | ----------- |
| P01 Chen FSE 2019        | 3.5      | quantitative | ~58 %          | —         | —            | —           |
| P02 Ghosh ICSE 2022      | 4.0      | quantitative | ~60 %          | ~60 %     | —            | —           |
| P03 Wang TSC 2021        | 3.5      | quantitative | —              | ~50 %\*   | —            | —           |
| P04 She ICSE-SEIP 2021   | 4.0      | quantitative | ~55 %          | ~60 %     | —            | —           |
| P05 Xu WWW 2018          | 2.5      | quantitative | detection only | —         | —            | —           |
| P06 Nedelkoski ECML 2020 | 2.5      | quantitative | detection only | —         | —            | —           |
| P07 Liu ICSOC 2022       | 3.5      | quantitative | 52 %           | 49 %      | —            | —           |
| P08 Shan SOSP 2019       | 4.0      | quantitative | —              | ~55 %     | —            | —           |
| P09 Wu NOMS 2020         | 3.5      | quantitative | —              | ~47 %\*   | —            | —           |
| P10 Ahmed IEEE ToN 2021  | 1.5      | theoretical  | tangential     | —         | —            | —           |
| P11 Khatuya ICSOC 2023   | 3.5      | quantitative | —              | ~58 %     | —            | —           |
| P12 Soldani CSUR 2022    | 3.5      | quantitative | ~50 %          | —         | —            | —           |
| P13 Dang ICSE 2019       | 3.0      | quantitative | ~45 %          | baseline  | —            | —           |
| P14 Zhang SANER 2024     | 4.0      | quantitative | ~63 %          | —         | —            | —           |
| P15 Li EuroSys 2023      | 4.0      | quantitative | —              | ~62 %     | —            | HITL        |
| P16 Cheng TSE 2023       | 4.0      | quantitative | ~48 %          | —         | XAI          | EU AI Act   |
| P17 Park ASE 2023        | 3.0      | quantitative | —              | —         | SCER/CV_MTTD | —           |
| P18 Peng SOCC 2022       | 3.5      | quantitative | —              | —         | —            | kill-switch |
| P19 Müller CCS 2023      | 2.5      | quantitative | —              | —         | —            | audit trail |

\*Inferred from resolution time or localization latency — QA1=PARTIAL.

---

## Extraction Protocol

1. **Primary extractor:** Lead researcher extracts all fields independently.
2. **Second reviewer:** Validates QA1–QA4 scores and RQ field values independently.
3. **Conflict resolution:** Disagreements resolved by consensus; if unresolved, conservative score applied (lower QAScore).
4. **Version control:** All extraction data committed to `src/research/quality_assessment.py` (machine-readable) and this document (human-readable).
5. **Inter-rater reliability:** Cohen's κ computed for QA1–QA4 after independent scoring; target κ ≥ 0.70.
