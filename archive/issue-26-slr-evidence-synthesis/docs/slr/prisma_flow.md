# PRISMA 2020 Flow — SLR Corpus P01–P19

> **Spec reference:** `specs/research/slr-evidence-synthesis.md`
> **Rules:** RULE-R01, RULE-R02, RULE-R03, RULE-R04, RULE-004
> **Last updated:** 2026-05-17 | Reviewer: Valdomiro de Oliveira Souza Júnior

This document records the PRISMA 2020 systematic review flow for the SLR corpus.
Machine-readable implementation: `src/research/slr_pipeline.py` (`run_prisma_flow()`).

---

## Search String (RULE-R01)

```
("Agentic AI" OR "Multi-Agent System*")
AND
("Incident Response" OR "Incident Management" OR "Incident Resolution"
 OR "HITL" OR "HOTL")
```

Any variation to this string requires a new ADR (RULE-R01).

---

## Databases Searched

| Database                   | Records retrieved | Period    |
| -------------------------- | ----------------- | --------- |
| ACM Digital Library        | 47                | 2018–2026 |
| IEEE Xplore                | 38                | 2018–2026 |
| Springer Link              | 29                | 2018–2026 |
| arXiv (cs.SE, cs.AI)       | 21                | 2020–2026 |
| Google Scholar (grey lit.) | 14                | 2020–2026 |
| **Total identified**       | **149**           |           |

---

## PRISMA 2020 Funnel

```
┌───────────────────────────────────────────────────────────┐
│  IDENTIFICATION                                           │
│  Records identified via database search: 149             │
│  Additional grey literature records: 14                  │
│  Total identified: 149 (inclusive of grey lit.)          │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│  SCREENING                                                │
│  Records after duplicate removal: 127                    │
│  Duplicates removed: 22                                  │
│                                                           │
│  Records screened (title/abstract): 127                  │
│  Excluded (off-topic, below venue rank, < 1 citation,    │
│  outside 2018–2026 window): 74                           │
│  Records retained: 53                                    │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│  ELIGIBILITY                                              │
│  Full texts assessed: 53                                  │
│  Excluded (full text unavailable): 4                     │
│  Excluded (does not address RQ1–RQ4): 21                 │
│  Excluded (QA total < 1.5 → theoretical only): 9        │
│  Papers passing eligibility: 19                          │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│  INCLUSION                                                │
│  Papers included in synthesis: 19 (P01–P19)              │
│                                                           │
│  Evidence tier partition (RULE-004):                     │
│    Quantitative (QA total ≥ 1.5): 18 papers             │
│    Theoretical context only (QA total < 1.5): 1 paper   │
│      → P10 Ahmed IEEE ToN 2021 (total = 1.5, boundary)  │
└───────────────────────────────────────────────────────────┘
```

> **Note on P10:** P10 scores exactly 1.5 (QA3=YES, QA4=PARTIAL, QA1=NO, QA2=NO),
> which meets the ≥ 1.5 threshold. It is classified as **quantitative** but cited only
> for network-routing context — never as primary evidence for MTTD/MTTR claims (RULE-003).

---

## Stage Counts (PRISMA 2020 Item 17a)

| Stage               | Count  |
| ------------------- | ------ |
| Identified          | 149    |
| After deduplication | 127    |
| Screened            | 53     |
| Full-text assessed  | 53     |
| Included            | 19     |
| Exclusion rate      | 87.2 % |

---

## Exclusion Reasons at Eligibility Stage

| Reason                   | Criterion | Count |
| ------------------------ | --------- | ----- |
| Full text not available  | EC6       | 4     |
| Does not address RQ1–RQ4 | EC4       | 21    |
| QA total < 1.5           | EC7       | 9     |

---

## Included Papers by Evidence Tier

### Quantitative Tier (QA ≥ 1.5, 18 papers)

| ID  | Paper                        | QA Total | Primary RQ    |
| --- | ---------------------------- | -------- | ------------- |
| P01 | Chen et al., FSE 2019        | 3.5      | RQ1, RQ2      |
| P02 | Ghosh et al., ICSE 2022      | 4.0      | RQ1, RQ2      |
| P03 | Wang et al., TSC 2021        | 3.5      | RQ2           |
| P04 | She et al., ICSE-SEIP 2021   | 4.0      | RQ1, RQ2      |
| P05 | Xu et al., WWW 2018          | 2.5      | RQ1           |
| P06 | Nedelkoski et al., ECML 2020 | 2.5      | RQ1           |
| P07 | Liu et al., ICSOC 2022       | 3.5      | RQ1, RQ2      |
| P08 | Shan et al., SOSP 2019       | 4.0      | RQ2           |
| P09 | Wu et al., NOMS 2020         | 3.5      | RQ2           |
| P10 | Ahmed et al., IEEE ToN 2021  | 1.5      | context only  |
| P11 | Khatuya et al., ICSOC 2023   | 3.5      | RQ2           |
| P12 | Soldani & Brogi, CSUR 2022   | 3.5      | RQ1, RQ2      |
| P13 | Dang et al., ICSE 2019       | 3.0      | RQ1, RQ2      |
| P14 | Zhang et al., SANER 2024     | 4.0      | RQ1, RQ2      |
| P15 | Li et al., EuroSys 2023      | 4.0      | RQ2, RQ4      |
| P16 | Cheng et al., TSE 2023       | 4.0      | RQ1, RQ3, RQ4 |
| P17 | Park et al., ASE 2023        | 3.0      | RQ3           |
| P18 | Peng et al., SOCC 2022       | 3.5      | RQ4           |
| P19 | Müller et al., CCS 2023      | 2.5      | RQ4           |

### Theoretical Tier (QA < 1.5, 0 papers in corpus P01–P19)

No paper in the final corpus P01–P19 falls below the 1.5 threshold.
Papers with QA total < 1.5 were excluded at the eligibility stage (EC7).

---

## Coverage by Research Question

| RQ                   | Papers                                           | Quantitative papers | Notes                                    |
| -------------------- | ------------------------------------------------ | ------------------- | ---------------------------------------- |
| RQ1 — MTTD reduction | P01, P02, P04, P05, P06, P07, P12, P13, P14, P16 | 10                  | P05/P06: detection only (QA2=NO)         |
| RQ2 — MTTR reduction | P02, P03, P04, P07, P08, P09, P11, P12, P13, P15 | 10                  |                                          |
| RQ3 — Bias/fairness  | P16, P17                                         | 2                   | P17 is primary; P16 supplementary        |
| RQ4 — Governance     | P15, P16, P18, P19                               | 4                   | P19: theoretical context for audit trail |

---

## Pre-2020 Exceptions (RULE-R02)

Three papers were published before the primary 2020–2026 coverage window and
retained by exception due to their foundational role and citation count:

| ID              | Year | Citations | Justification                                                  |
| --------------- | ---- | --------- | -------------------------------------------------------------- |
| P01 Chen et al. | 2019 | 312       | Foundational MTTD/MTTR baseline for Microsoft Azure production |
| P08 Shan et al. | 2019 | 267       | Foundational autonomous RCA study at SOSP                      |
| P13 Dang et al. | 2019 | 389       | Industry MTTD/MTTR baseline survey from Microsoft              |

Each exception is documented and justified. No additional pre-2020 papers are admitted
without a new ADR (RULE-R02, RULE-006).
