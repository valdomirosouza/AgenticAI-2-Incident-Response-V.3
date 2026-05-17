# Skill: AI Ethics

**Domain**: ethics
**Activation triggers**: AI ethics, EU AI Act, NIST AI RMF, IEEE 7000, value alignment, transparency, XAI, explainability, accountability, human oversight, high-risk AI
**References**: specs/ethics/16-autonomy-boundaries.md, specs/ethics/17-audit-trail.md, ADR-0023, ADR-0026

---

## Compliance Baseline

| Standard / Regulation        | Domain enforced                                   |
| ---------------------------- | ------------------------------------------------- |
| **EU AI Act** Arts. 9, 12–14 | Risk management, logging, human oversight         |
| **NIST AI RMF**              | AI risk governance — GOVERN, MAP, MEASURE, MANAGE |
| **IEEE 7000**                | Algorithmic impact assessment, value alignment    |
| **SOC 2 CC7**                | Audit logging of system activity                  |

---

## EU AI Act — Article-by-Article Mapping

### Art. 9 — Risk Management System

A continuous risk management system must be maintained throughout the AI system lifecycle:

| Risk management element     | Implementation                                                               |
| --------------------------- | ---------------------------------------------------------------------------- |
| Risk identification         | STRIDE + LLM extensions threat model (ADR-0016, spec 11)                     |
| Risk estimation             | DPIA/RIPD risk register (spec 21, Part C) — 10 identified risks              |
| Risk evaluation             | Residual risk assessed per risk; no unmitigated Critical/High residual risks |
| Risk mitigation measures    | Technical controls per ADR-0014, ADR-0021–ADR-0028; HITL gate (ADR-0023)     |
| Testing                     | SAST gates G04/G05, DAST staging gate, quarterly bias audit (ADR-0026)       |
| Residual risk communication | Confidence score + `[LOW CONFIDENCE]` label surfaced to operator             |

### Art. 12 — Record-Keeping

High-risk AI systems must automatically log events for post-hoc oversight:

- **Requirement**: logging of system operation periods, input data references, decision sequences
- **Implementation**: immutable append-only hash-chained audit trail (spec 17, ADR-0024)
- **Event coverage**: all 22 event types in the audit vocabulary cover the full incident lifecycle
- **Retention**: 2-year minimum per GCS WORM Object Lock (spec 20)

### Art. 13 — Transparency and Information Provision

Operators must understand the AI system's capabilities and limitations:

| Transparency measure     | Implementation                                                                  |
| ------------------------ | ------------------------------------------------------------------------------- |
| Confidence scores        | Every `rca.hypothesis_set` and `remediation.proposed` event includes confidence |
| Low-confidence label     | `[LOW CONFIDENCE: XX%]` prepended to output when confidence < 0.6 (ADR-0021)    |
| `AI-GENERATED` label     | All LLM-generated recommendations carry this label before operator review       |
| Capability documentation | CLAUDE.md §1.3 system boundaries; spec 01 (agent architecture)                  |
| Limitation documentation | BLOCKED action list (spec 16 §3.2); HOTL vs. HITL distinction                   |

### Art. 14 — Human Oversight

High-risk AI systems must allow effective oversight by natural persons:

| Art. 14 requirement                     | Implementation                                                          |
| --------------------------------------- | ----------------------------------------------------------------------- |
| Override capability at any time         | Engineer can reject any HITL proposal; kill-switch available (ADR-0025) |
| Monitoring during operation             | HOTL for detection/triage/RCA — all decisions surfaced in real time     |
| Understanding of system capabilities    | Confidence scores + `AI-GENERATED` labels on all outputs                |
| Ability to disregard, override, reverse | Remediation rejection returns to human-managed workflow                 |
| Not overriding human oversight          | No auto-execute on timeout; BLOCKED actions are architectural limits    |

---

## NIST AI RMF — Function Mapping

| AI RMF Function | Activity                        | This project                                                        |
| --------------- | ------------------------------- | ------------------------------------------------------------------- |
| **GOVERN**      | Policies and accountability     | CLAUDE.md §5 rules; HITL/HOTL policy (spec 16); DPIA/RIPD (spec 21) |
| **MAP**         | Context and risk identification | Threat model (spec 11); PII inventory (spec 19); STRIDE analysis    |
| **MEASURE**     | Analysis and metrics            | Bias audit (spec 18); MTTD/MTTR metrics; confidence threshold gate  |
| **MANAGE**      | Risk response                   | HITL gate (ADR-0023); kill-switch (ADR-0025); quarterly bias audit  |

---

## IEEE 7000 — Value Alignment Checklist

Run during any design review that touches agent decision logic:

- [ ] Agent values are traceable to stakeholder values (incident responders, end users, organisation)
- [ ] Value conflicts are documented and resolved in ADRs — never silently ignored
- [ ] System cannot pursue a goal at the expense of human well-being (BLOCKED action enforcement)
- [ ] Autonomy level matches the risk level of the action (HOTL for triage; HITL for remediation)
- [ ] System respects human decision authority — no auto-execution on timeout

---

## Explainability (XAI) Requirements

Every agent output that informs a human decision must include an explanation:

| Output type           | Explanation provided                                    | Where                           |
| --------------------- | ------------------------------------------------------- | ------------------------------- |
| RCA hypothesis        | Root cause + contributing evidence + confidence score   | `RCAHypothesis.explanation`     |
| Remediation proposal  | Proposed action + predicted effect + risk estimate      | `RemediationProposal.rationale` |
| Low-confidence output | `[LOW CONFIDENCE: XX%]` prefix + reason for uncertainty | Confidence gate (ADR-0021)      |
| HITL approval request | Full proposal context shown before engineer approves    | HITL approval UI                |

**Key invariant**: No LLM-generated output reaches an operator without an explanation. Raw model output is rejected as a `LLMOutputInvalid` exception.

---

## Accountability Framework

| Accountability layer  | Responsible party           | Mechanism                                                |
| --------------------- | --------------------------- | -------------------------------------------------------- |
| System design         | Tech Lead                   | ADRs, specs, DPIA/RIPD sign-off                          |
| Data protection       | DPO (Tech Lead)             | DPIA/RIPD (spec 21); ANPD/GDPR notification (PRIVACY.md) |
| Bias auditing         | Tech Lead + Ethics reviewer | Quarterly audit (spec 18); release gate (ADR-0026)       |
| Runtime decisions     | On-call engineer            | HITL approval required for all PRODUCTION\_\* actions    |
| Audit trail integrity | `audit_adapter` service     | Hash chain + nightly integrity check (spec 17)           |
| Kill-switch           | Any engineer (emergency)    | ADR-0025 — RTO < 60 seconds                              |

---

## AI Ethics Review Checklist

Run during any PR that introduces or modifies agent decision logic:

- [ ] EU AI Act Art. 14: operator retains ability to override or reject any agent output
- [ ] EU AI Act Art. 13: output includes confidence score and `AI-GENERATED` label
- [ ] EU AI Act Art. 12: all relevant events are covered by audit trail vocabulary (spec 17 §3.3)
- [ ] NIST AI RMF: new risk introduced? If yes, update DPIA/RIPD risk register
- [ ] IEEE 7000: new agent capability does not pursue efficiency at the expense of safety
- [ ] Value alignment: new action type is classified in the HITL/HOTL matrix (spec 16 §3.2)
