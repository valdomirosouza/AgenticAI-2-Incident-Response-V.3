# Spec 22: Anonymization Standard

**Domain**: privacy
**Owner**: DPO / Privacy Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #14
**Linked ADRs**: ADR-0031, ADR-0032
**Review cadence**: Before every production deploy with PII changes; DPO + Legal required

---

## 1. Purpose

Define the anonymization technique per dataset type, quality validation procedure,
re-identification risk test thresholds, and the reproducible pipeline that produces
the evaluation corpus for the dissertation research.

---

## 2. Context

ADR-0031 established k-anonymity (k ≥ 5), re-identification risk < 5% and utility ≥
80% as the quality gates for any dataset used in dissertation evaluation. Truly
anonymised data falls outside LGPD art. 12 and GDPR Recital 26 scope, simplifying
ongoing compliance. This spec translates the ADR into a step-by-step technique
selection guide and validation procedure.

---

## 3. Decision

### 3.1 Technique selection by dataset type

| Dataset type              | Anonymization technique                                       | Tool(s)                                     | Rationale                                                           |
| ------------------------- | ------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------- |
| **Log fixtures** (JSON)   | PII field replacement + k-anonymity on quasi-identifiers      | Presidio v2 + ARX anonymizer                | IP → subnet; `user_id` → synthetic opaque ID; timestamps → hour     |
| **Incident timelines**    | Role substitution + entity generalisation                     | Custom script (`anonymization_pipeline.py`) | Engineer names → `engineer_<hash>`; service names → `svc_<cat>_<N>` |
| **Metric time series**    | Aggregation + Gaussian noise injection (differential privacy) | Google DP Library                           | Per-user metrics → service-level; ε = 1.0 (Gaussian mechanism)      |
| **Runbook content**       | Named entity removal                                          | spaCy NER + Presidio                        | URLs → `[REDACTED_URL]`; hostnames → `[REDACTED_HOST]`              |
| **Distributed traces**    | Trace ID regeneration + attribute scrubbing                   | Custom OTel processor                       | Original `trace_id`/`span_id` → synthetic IDs; `user.id` removed    |
| **Post-mortem documents** | Role label substitution + temporal generalisation             | Custom script                               | Real timestamps → relative offsets; role labels → generic roles     |

### 3.2 Anonymization pipeline

All evaluation datasets pass through this pipeline before use in any analysis, model
evaluation or dissertation result:

```
Raw incident data (may contain PII)
        │
        ▼
Step 1  PII Detection
        Presidio AnalyzerEngine (en + pt, score ≥ 0.7)
        + spaCy NER (en_core_web_lg model)
        + Custom regex pass (CPF, CNPJ, IPv6, BR phone)
        │
        ▼
Step 2  Field-level anonymization
        Per technique selection table (§3.1)
        Replacement / generalisation / aggregation / noise injection
        │
        ▼
Step 3  k-anonymity check (ARX)
        If k < 5: re-anonymize or exclude record
        Log: k value achieved, quasi-identifier combination
        │
        ▼
Step 4  Re-identification risk check (ARX risk model)
        If risk > 5%: apply suppression to high-risk records
        Log: risk score before and after suppression
        │
        ▼
Step 5  Utility check
        Run downstream ML metrics on anonymised corpus
        If utility < 80%: flag for manual review
        Log: utility score, metric used
        │
        ▼
Anonymised corpus → evaluation pipeline
        │
        ▼
Step 6  Anonymization report (JSON)
        Stored in data/audit/anon-report-<corpus>-<date>.json
```

The pipeline is implemented in `src/research/anonymization_pipeline.py`. Each run is
deterministic given the same seed — outputs are reproducible.

### 3.3 Quality thresholds

| Criterion                  | Threshold | Test                                                            | Action on failure                                                 |
| -------------------------- | --------- | --------------------------------------------------------------- | ----------------------------------------------------------------- |
| **k-anonymity**            | k ≥ 5     | ARX: no quasi-identifier combination appears fewer than 5 times | Re-anonymize or exclude record                                    |
| **Re-identification risk** | < 5%      | ARX singling-out risk model (journalist attack)                 | Suppress high-risk records                                        |
| **Utility preservation**   | ≥ 80%     | Downstream ML metric on anonymised vs. raw corpus               | Manual review; lower threshold only with documented justification |

If the 80% utility threshold cannot be met, the dataset switches to the pseudonymised
path (§3.4) rather than lowering the threshold unilaterally.

### 3.4 Residual pseudonymised data path

Where true anonymization degrades utility below 80% (e.g. fine-grained timestamps
needed for MTTD measurement):

| Step | Action                                                                                         |
| ---- | ---------------------------------------------------------------------------------------------- |
| 1    | Apply pseudonymization: replace identifiers with synthetic keys                                |
| 2    | Store mapping table (original → synthetic) encrypted in Vault (ADR-0020), **never in repo**    |
| 3    | Apply to the pseudonymised corpus: all same anonymization steps except temporal generalisation |
| 4    | Retain pseudonymised corpus only for dissertation duration (ADR-0030)                          |
| 5    | Destroy mapping table immediately after thesis defence; record `audit.mapping_table_destroyed` |

Pseudonymised data remains subject to LGPD/GDPR. Legal basis: LGPD art. 7 XIV +
art. 23 (research); GDPR art. 89 (research exemption).

### 3.5 Differential privacy parameters

For metric time series anonymisation (Google DP Library):

| Parameter   | Value         | Justification                                                                 |
| ----------- | ------------- | ----------------------------------------------------------------------------- |
| Mechanism   | Gaussian      | Continuous-valued metrics (latency, error rate) — Gaussian noise appropriate  |
| ε (epsilon) | 1.0           | Standard research setting; balances privacy and utility for aggregate metrics |
| δ (delta)   | 1e-6          | Standard setting for Gaussian mechanism                                       |
| Sensitivity | Per-metric    | Calibrated to the range of the specific metric (e.g. latency in ms)           |
| Aggregation | Service-level | Per-user metrics aggregated before noise; minimises sensitivity               |

ε = 1.0 is a reasonable privacy budget for academic research where data subjects are
not individually targeted and the corpus is used for aggregate MTTD/MTTR measurement.

### 3.6 Anonymization report schema

Each pipeline run produces a report at `data/audit/anon-report-<corpus>-<date>.json`:

```json
{
  "corpus_id": "incidents-2026-Q1",
  "run_date": "2026-05-17",
  "dataset_type": "log_fixtures",
  "technique": "pii_replacement_k_anonymity",
  "records_input": 1250,
  "records_output": 1218,
  "records_excluded": 32,
  "k_achieved": 7,
  "k_threshold": 5,
  "k_pass": true,
  "reid_risk": 0.032,
  "reid_threshold": 0.05,
  "reid_pass": true,
  "utility_score": 0.87,
  "utility_threshold": 0.8,
  "utility_pass": true,
  "overall_pass": true,
  "pseudonymised_fallback": false,
  "notes": ""
}
```

A report with `overall_pass: false` blocks the corpus from entering the evaluation
pipeline. The CI release gate checks that all corpora referenced by evaluation scripts
have a passing report dated within the last 6 months.

### 3.7 Re-identification risk test procedure

The ARX singling-out risk test uses the "journalist attack" model (worst-case):

1. Define quasi-identifier set: {timestamp_hour, service_name, error_code, user_id_prefix}
2. Run ARX risk analysis: compute the probability that a specific record can be singled
   out by an adversary with access to the quasi-identifiers.
3. If maximum individual risk > 5%: suppress the highest-risk records (remove from corpus).
4. Re-run until overall risk ≤ 5%.

Quasi-identifiers are documented per corpus in the anonymization report. Any change to
the quasi-identifier set requires a new pipeline run and a new report.

### 3.8 Privacy Impact

- Truly anonymised datasets (k ≥ 5, risk < 5%) fall outside LGPD art. 12 / GDPR
  Recital 26 scope — no ongoing consent or legal basis required for analysis.
- Pseudonymised fallback datasets remain in scope — legal basis is LGPD art. 7 XIV
  - art. 23 / GDPR art. 89.
- Mapping tables are never committed to the repository (RULE-C03); they live only in
  Vault (ADR-0020) and are destroyed after thesis defence.
- DP noise injection (ε = 1.0) provides mathematical privacy guarantees for metric
  time series — no individual's contribution can be inferred from the aggregate.

---

## 4. Acceptance Criteria

- [ ] Technique selection table covers all 6 dataset types with tool and rationale
- [ ] 5-step anonymization pipeline documented with ARX quality gates at steps 3 and 4
- [ ] Quality thresholds: k ≥ 5, re-ID risk < 5%, utility ≥ 80% — each with test method and failure action
- [ ] Pseudonymised fallback path documented with mapping table in Vault and destruction after defence
- [ ] DP parameters table: ε = 1.0, δ = 1e-6, Gaussian mechanism, per-metric sensitivity
- [ ] Anonymization report JSON schema defined with all required fields including `overall_pass`
- [ ] Re-identification risk test procedure names ARX journalist attack model
- [ ] DPO / Privacy Lead + Legal review recorded before merge
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                                 |
| -------- | ------------------------------------------------------------------------- |
| ADR-0020 | Vault — pseudonymised mapping table stored in Vault, never in repo        |
| ADR-0028 | Presidio — reused in Step 1 (PII detection) of the anonymization pipeline |
| ADR-0029 | DPIA/RIPD — anonymization report is evidence for Part D                   |
| ADR-0030 | Data retention — pseudonymised corpus deleted at dissertation end         |
| ADR-0031 | Anonymization standard — technique selection, quality gates, DP params    |
| ADR-0032 | Cross-border transfers — anonymised data has no transfer risk             |

---

## References

- LGPD (Lei 13.709/2018) Art. 12 — Anonymised data; Art. 7 XIV; Art. 23 — Research basis
- GDPR (EU 2016/679) Recital 26 — Anonymised data; Art. 89 — Research exemption
- ARX Data Anonymization Tool — arx.deidentifier.org
- Google Differential Privacy Library — github.com/google/differential-privacy
- Microsoft Presidio v2 — github.com/microsoft/presidio
- `docs/adr/ADR-0031-anonymization-standard-agent-datasets.md`
- `specs/privacy/21-dpia-ripd.md` — R-10 (re-identification risk) mitigated by this standard
- `src/research/anonymization_pipeline.py` — pipeline implementation (Phase 5)
