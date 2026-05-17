# Skill: Anonymization

**Domain**: privacy
**Activation triggers**: anonymization, pseudonymization, k-anonymity, differential privacy, tokenization, ARX, re-identification risk, data drift, research corpus, anonymization pipeline, Presidio anonymizer, DP epsilon, utility threshold
**References**: specs/privacy/22-anonymization-standard.md, ADR-0031

---

## Technique Selection by Dataset Type

| Dataset type              | Technique                                                | Tool(s)                                     |
| ------------------------- | -------------------------------------------------------- | ------------------------------------------- |
| **Log fixtures** (JSON)   | PII field replacement + k-anonymity on quasi-identifiers | Presidio v2 + ARX anonymizer                |
| **Incident timelines**    | Role substitution + entity generalisation                | Custom script (`anonymization_pipeline.py`) |
| **Metric time series**    | Aggregation + Gaussian noise (differential privacy)      | Google DP Library                           |
| **Runbook content**       | Named entity removal                                     | spaCy NER + Presidio                        |
| **Distributed traces**    | Trace ID regeneration + attribute scrubbing              | Custom OTel processor                       |
| **Post-mortem documents** | Role label substitution + temporal generalisation        | Custom script                               |

---

## Anonymization Pipeline (5 Steps)

All evaluation datasets must pass through this pipeline before any analysis, model evaluation, or dissertation result:

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
        Per technique selection table above
        Replacement / generalisation / aggregation / noise injection
        │
        ▼
Step 3  k-anonymity check (ARX)
        If k < 5: re-anonymize or exclude record
        Log: k value achieved, quasi-identifier combination
        │
        ▼
Step 4  Re-identification risk check (ARX journalist attack model)
        If risk > 5%: suppress high-risk records
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

The pipeline is implemented in `src/research/anonymization_pipeline.py`. Each run is deterministic given the same seed — outputs are reproducible.

---

## Quality Thresholds

| Criterion                  | Threshold | Test                                                            | Action on failure                                     |
| -------------------------- | --------- | --------------------------------------------------------------- | ----------------------------------------------------- |
| **k-anonymity**            | k ≥ 5     | ARX: no quasi-identifier combination appears fewer than 5 times | Re-anonymize or exclude record                        |
| **Re-identification risk** | < 5%      | ARX singling-out risk model (journalist attack)                 | Suppress high-risk records                            |
| **Utility preservation**   | ≥ 80%     | Downstream ML metric on anonymised vs. raw corpus               | Manual review; switch to pseudonymised path if needed |

If the 80% utility threshold cannot be met, the dataset switches to the pseudonymised path rather than lowering the threshold.

---

## Differential Privacy Parameters (Metric Time Series)

| Parameter   | Value         | Justification                                                                   |
| ----------- | ------------- | ------------------------------------------------------------------------------- |
| Mechanism   | Gaussian      | Continuous-valued metrics (latency ms, error rate) — Gaussian noise appropriate |
| ε (epsilon) | 1.0           | Standard research setting; balances privacy and utility for aggregate metrics   |
| δ (delta)   | 1e-6          | Standard for Gaussian mechanism                                                 |
| Sensitivity | Per-metric    | Calibrated to the range of the specific metric                                  |
| Aggregation | Service-level | Per-user metrics aggregated before noise; minimises sensitivity                 |

```python
from google.cloud import dp

def add_gaussian_noise(values: list[float], sensitivity: float, epsilon: float = 1.0) -> list[float]:
    dp_mechanism = dp.GaussianMechanism(
        epsilon=epsilon,
        delta=1e-6,
        l2_sensitivity=sensitivity,
    )
    return [dp_mechanism.add_noise(v) for v in values]
```

---

## Anonymization Report Schema

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

A report with `overall_pass: false` blocks the corpus from entering the evaluation pipeline. CI release gate checks all corpora referenced by evaluation scripts have a passing report dated within the last 6 months.

---

## Re-Identification Risk Test Procedure (ARX Journalist Attack)

1. Define quasi-identifier set: `{timestamp_hour, service_name, error_code, user_id_prefix}`
2. Run ARX risk analysis: compute probability that a specific record can be singled out by an adversary with access to the quasi-identifiers
3. If maximum individual risk > 5%: suppress the highest-risk records (remove from corpus)
4. Re-run until overall risk ≤ 5%

Quasi-identifiers are documented per corpus in the anonymization report. Any change to the quasi-identifier set requires a new pipeline run and a new report.

---

## Pseudonymised Fallback Path

When true anonymization degrades utility below 80% (e.g. fine-grained timestamps needed for MTTD measurement):

| Step | Action                                                                                  |
| ---- | --------------------------------------------------------------------------------------- |
| 1    | Apply pseudonymization: replace identifiers with synthetic keys                         |
| 2    | Store mapping table (original → synthetic) encrypted in Vault — **never in repository** |
| 3    | Apply same anonymization steps except temporal generalisation                           |
| 4    | Retain pseudonymised corpus only for dissertation duration (ADR-0030)                   |
| 5    | Destroy mapping table after thesis defence; emit `audit.mapping_table_destroyed`        |

Pseudonymised data remains subject to LGPD/GDPR. Legal basis: LGPD art. 7 XIV + art. 23 / GDPR art. 89.

---

## Running the Pipeline

```shell
# Run anonymization pipeline on a new corpus
python src/research/anonymization_pipeline.py \
  --input data/raw/incidents-2026-Q1.json \
  --output data/anonymised/incidents-2026-Q1-anon.json \
  --report data/audit/anon-report-incidents-2026-Q1.json \
  --seed 42

# Validate the report passes quality gates
python harness/scripts/check_anon_report.py \
  data/audit/anon-report-incidents-2026-Q1.json

# ARX risk analysis (requires ARX CLI)
arx -d data/raw/incidents-2026-Q1.csv \
    -qi timestamp_hour service_name error_code \
    -k 5 \
    --risk-threshold 0.05 \
    --output data/audit/arx-report.json
```

---

## Anonymization Checklist

Before using any dataset in analysis or evaluation:

- [ ] Dataset has passed the 5-step anonymization pipeline
- [ ] Anonymization report exists and `overall_pass: true`
- [ ] Report dated within last 6 months (CI gate)
- [ ] k ≥ 5 achieved — quasi-identifier set documented in report
- [ ] Re-identification risk < 5% (journalist attack model)
- [ ] Utility ≥ 80% — or pseudonymised fallback path documented
- [ ] If pseudonymised: mapping table in Vault only, not in repository (RULE-C03)
- [ ] DP parameters (ε = 1.0, δ = 1e-6) used for any metric time series
