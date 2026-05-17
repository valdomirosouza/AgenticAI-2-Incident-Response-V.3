# ADR-0031: Anonymization Standard for Agent Training and Evaluation Datasets

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / DPO / Privacy Lead — researcher)
**Affected RQs**: RQ2 (evaluation methodology), RQ4 (privacy compliance)

---

## Context

The dissertation evaluation requires a corpus of real or realistic incidents to measure
MTTD and MTTR improvement (CLAUDE.md §1.6 criterion 1). This corpus contains:

- Historical incident records (timelines, alert sequences, metric snapshots)
- Post-mortem documents (may contain engineer role references, service names, CUJ details)
- Runbook content (may reference internal service endpoints and team names)
- Log fixtures (may contain `user_id`, IP addresses, request parameters)

Two legal frameworks regulate how this data may be used:

- **LGPD art. 12** — anonymised data (data that cannot be re-identified, individually
  or in aggregate) is not subject to LGPD. Pseudonymised data (reversible) remains
  subject to LGPD and requires a legal basis.
- **GDPR Recital 26** — the same principle: truly anonymised data falls outside the
  regulation's scope. The anonymization must be irreversible using "all means
  reasonably likely to be used".

The research compliance strategy is: anonymise evaluation fixtures before ingestion into
any analysis pipeline. If true anonymization is not achievable for a data category,
pseudonymization with a separate mapping key is the fallback — but it remains in scope
for LGPD/GDPR.

## Decision

All agent training and evaluation datasets are processed through a defined anonymization
pipeline before use in any analysis, model evaluation or dissertation result.

### Anonymization technique selection by dataset type

| Dataset type                         | Technique                                                | Tool                                 | Rationale                                                                                         |
| ------------------------------------ | -------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------- |
| **Log fixtures** (structured JSON)   | PII field replacement + k-anonymity on quasi-identifiers | Presidio (ADR-0028) + ARX anonymizer | IP addresses → `10.x.x.x/24` subnets; `user_id` → synthetic opaque ID; timestamps rounded to hour |
| **Incident timelines** (post-mortem) | Role substitution + entity generalisation                | Custom script                        | Engineer names → `engineer_<hash>` roles; service names → `svc_<category>_<N>`                    |
| **Metric time series**               | Aggregation + noise injection (differential privacy)     | Google DP Library                    | Raw per-user metrics aggregated to service-level; Gaussian noise ε=1.0                            |
| **Runbook content**                  | Named entity removal                                     | spaCy NER + Presidio                 | Service URLs → `[REDACTED_URL]`; internal hostnames → `[REDACTED_HOST]`                           |
| **Distributed traces**               | Trace ID regeneration + attribute scrubbing              | Custom OTel processor                | Original `trace_id`/`span_id` replaced with synthetic IDs; user attributes removed                |

### Anonymization quality criteria

For each dataset, anonymization quality is assessed before the corpus is finalised:

| Criterion                  | Threshold | Test                                                                        |
| -------------------------- | --------- | --------------------------------------------------------------------------- |
| **k-anonymity**            | k ≥ 5     | No quasi-identifier combination appears fewer than 5 times                  |
| **Re-identification risk** | < 5%      | Singling-out risk assessed with ARX re-identification tool                  |
| **Utility preservation**   | ≥ 80%     | Downstream ML metrics on anonymised corpus within 80% of raw corpus metrics |

If any criterion is not met, the dataset is either further anonymised or excluded from
the evaluation corpus.

### Residual pseudonymized data

Where true anonymization degrades utility below 80% (e.g. fine-grained timestamps
required for MTTD measurement), the data is pseudonymised:

- A mapping table (original → synthetic ID) is stored separately, encrypted, in Vault
  (ADR-0020), never in the repository.
- The pseudonymised corpus is retained only for the dissertation duration (ADR-0030).
- The mapping table is destroyed after the thesis defence.

Pseudonymised data remains subject to LGPD/GDPR — legal basis: research (LGPD art. 7,
XIV and art. 23; GDPR art. 89 research exemption).

### Anonymization pipeline execution

```
Raw incident data
      │
      ▼
1. PII detection (Presidio + spaCy NER)
      │
      ▼
2. Field-level anonymization (replacement / generalisation / aggregation)
      │
      ▼
3. k-anonymity check (ARX) — if k < 5: re-anonymize or exclude record
      │
      ▼
4. Re-identification risk check — if risk > 5%: apply suppression
      │
      ▼
5. Utility check — if utility < 80%: flag for manual review
      │
      ▼
Anonymized corpus → evaluation pipeline
```

The pipeline is a reproducible Python script in `src/research/anonymization_pipeline.py`
(to be authored in Phase 5). Each run produces an anonymization report documenting
the technique applied, k value achieved, re-identification risk score and utility score.

## Alternatives Considered

| Alternative                                           | Pros                                                                              | Cons                                                                                                                                    |
| ----------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Synthetic data only**                               | Zero privacy risk; infinite generation                                            | Does not reflect real incident distributions; RULE-003 prohibits toy examples as quantitative evidence                                  |
| **Raw data with access controls**                     | Maximum utility                                                                   | LGPD art. 12 / GDPR Recital 26 — pseudonymised data remains in scope; requires DPIA/RIPD and data subject consent or research exemption |
| **Anonymization with k-anonymity + utility check** ✅ | LGPD/GDPR compliant if k ≥ 5; preserves evaluation utility; reproducible pipeline | Anonymization reduces some signal fidelity — mitigated by 80% utility threshold                                                         |

## Consequences

**Positive:**

- LGPD art. 12 / GDPR Recital 26: datasets meeting k ≥ 5 and re-identification risk
  < 5% fall outside LGPD/GDPR scope — simplifies ongoing compliance.
- Anonymization report per corpus run provides evidence for the DPIA/RIPD (ADR-0029)
  and the dissertation appendix.
- Reproducible pipeline ensures evaluation is replicable by future researchers.

**Negative / Trade-offs:**

- k-anonymity + differential privacy may reduce MTTD measurement precision for
  fine-grained timestamp analysis. Residual pseudonymization path provides the fallback.
- ARX and Google DP Library add Python dependencies — included in `requirements.in`
  and hash-pinned (ADR-0022).

## Review Criteria

Revisit this decision if:

- The 80% utility threshold causes the evaluation corpus to be too small for
  statistically significant results — lower the threshold with documented justification.
- ANPD publishes guidance on k-anonymity thresholds for AI research datasets.

## References

- LGPD (Lei 13.709/2018) Art. 12 — Anonymised data; Art. 7 XIV, Art. 23 — Research basis
- GDPR (EU 2016/679) Recital 26 — Anonymised data; Art. 89 — Research exemption
- ARX Data Anonymization Tool — arx.deidentifier.org
- Google Differential Privacy Library — github.com/google/differential-privacy
- `docs/adr/ADR-0028-pii-sanitization-llm-apis.md` — Presidio (reused in anonymization)
- `docs/adr/ADR-0029-dpia-ripd-before-production.md` — DPIA references this standard
- `docs/adr/ADR-0030-data-retention-ttl-policy.md` — research corpus retention
- `specs/privacy/22-anonymization-standard.md` — full anonymization spec (to be authored, issue #14)
