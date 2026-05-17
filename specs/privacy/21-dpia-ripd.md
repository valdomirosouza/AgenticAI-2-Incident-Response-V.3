# Spec 21: DPIA / RIPD — Data Protection Impact Assessment

**Domain**: privacy
**Owner**: DPO / Privacy Lead
**Status**: Approved — DPO Sign-off: Valdomiro de Oliveira Souza Júnior, 2026-05-17
**Date**: 2026-05-17
**Issue**: #14
**Linked ADRs**: ADR-0029
**Review cadence**: Before every production deploy with PII changes; DPO + Legal required

> **Hard gate**: No production deployment handling real incident data proceeds without
> this document being complete, signed and passing `check_dpia_completeness.py`
> (ADR-0029, CLAUDE.md §1.6 criterion 4).

---

## 1. Purpose

Fulfil the mandatory DPIA (GDPR art. 35) and RIPD (LGPD art. 38) obligations before
any production deployment of the Agentic AI Copilot that processes real incident data
containing personal data.

---

## 2. Context

The Copilot is a new-technology AI system that systematically processes personal data
(user IDs, IP addresses, request metadata, CPF in log payloads) at scale in the course
of incident response. GDPR art. 35 and LGPD art. 38 independently require a formal
impact assessment before such processing begins. EU AI Act Art. 9 requires a risk
management system for high-risk AI.

This document is structured per ADR-0029's six-section mandate and satisfies both
regulatory frameworks simultaneously.

---

## 3. Decision

### Part A — Processing Description (GDPR art. 35(7)(a), LGPD art. 38 I)

#### A.1 Processing purposes

| Purpose ID | Purpose                                                      | Agent(s) involved              | Legal basis (LGPD)              | Legal basis (GDPR)                 |
| ---------- | ------------------------------------------------------------ | ------------------------------ | ------------------------------- | ---------------------------------- |
| P-01       | Detect anomalies in observability data to identify incidents | DetectionAgent                 | Art. 7 IX (legitimate interest) | Art. 6(1)(f) (legitimate interest) |
| P-02       | Classify incident severity and notify on-call engineers      | TriageAgent                    | Art. 7 IX                       | Art. 6(1)(f)                       |
| P-03       | Construct root cause hypothesis from logs/traces             | RCAAgent                       | Art. 7 IX                       | Art. 6(1)(f)                       |
| P-04       | Propose and execute (HITL-approved) remediation actions      | RemediationAgent               | Art. 7 IX                       | Art. 6(1)(f)                       |
| P-05       | Draft blameless post-mortems from incident timelines         | PostMortemAgent                | Art. 7 IX                       | Art. 6(1)(f)                       |
| P-06       | Research evaluation — measure MTTD/MTTR improvement          | All agents (anonymised corpus) | Art. 7 XIV + Art. 23 (research) | Art. 89 (research)                 |

#### A.2 Data categories

Full inventory in `specs/privacy/19-pii-inventory.md`. Summary:

| Category             | Processing purpose(s) | Retention          | Masking applied                |
| -------------------- | --------------------- | ------------------ | ------------------------------ |
| `user_id` (PII-01)   | P-01, P-02, P-03      | 90 days (logs)     | Pseudonymised `usr_<hash>`     |
| IP address (PII-02)  | P-01, P-02, P-03      | 90 days (logs)     | Subnet mask `10.x.x.0/24`      |
| Email (PII-03)       | P-02 (on-call notify) | 14 days (traces)   | `[MASKED_EMAIL]`               |
| Person name (PII-04) | P-05 (post-mortem)    | 90 days post-close | Role label `engineer_alpha`    |
| CPF (PII-05)         | P-01, P-03 (in logs)  | 90 days (logs)     | `[MASKED_CPF]` via Presidio BR |
| CNPJ (PII-06)        | P-01, P-03 (in logs)  | 90 days (logs)     | `[MASKED_CNPJ]`                |
| Phone (PII-07)       | P-01 (in logs)        | 90 days (logs)     | `[MASKED_PHONE]`               |

#### A.3 Data flows

See `specs/system/01-system-architecture.md` §3.4 (PII boundary data flow diagram)
and `specs/privacy/19-pii-inventory.md` §3.2 (Data Flow Diagram).

Key data flows involving PII:

1. Raw observability data → OTel SpanProcessor (PII masked) → Loki/Tempo
2. Masked log/trace excerpts → OrchestratorAgent → Presidio sanitizer → Anthropic API
3. Pseudonymised incident data → Audit trail (GCS WORM)
4. Post-mortem drafts (role labels only) → PostMortemAgent → human review

#### A.4 Retention periods

Per `specs/privacy/20-data-retention-policy.md`:

- Operational logs: 90 days | Traces: 14 days | Audit trail: 2 years minimum
- LLM prompts: **never persisted** | Research corpus: dissertation + 5 years (anonymised)

#### A.5 Recipients

Per ADR-0032 transfer register:

| Recipient        | Country | Data category                           | Safeguard                       |
| ---------------- | ------- | --------------------------------------- | ------------------------------- |
| Anthropic Claude | USA     | Sanitized prompts (no PII per ADR-0028) | SCCs Module 1 + LGPD art. 33 VI |
| GitHub Actions   | USA     | Source code, CI logs (no PII, RULE-C03) | SCCs Module 1 + GitHub DPA      |
| GCS (audit)      | EU/US   | Pseudonymised audit records             | SCCs if non-EU; adequacy if EU  |

#### A.6 Technical controls

| Control                          | Implemented by                   | ADR      | Status   |
| -------------------------------- | -------------------------------- | -------- | -------- |
| PII masking — observability      | OTel SpanProcessor               | ADR-0014 | Designed |
| PII sanitization — LLM prompts   | Presidio + `sanitized=True` gate | ADR-0028 | Designed |
| LLM prompts never persisted      | `LLMAdapter` design              | ADR-0030 | Designed |
| HITL gate for production actions | ApprovalToken (HMAC-SHA256)      | ADR-0023 | Designed |
| Immutable audit trail            | GCS WORM + hash chain            | ADR-0024 | Designed |
| Data minimisation default        | Opt-in field collection          | ADR-0027 | Designed |
| Encryption at rest               | GCS default encryption (AES-256) | —        | Platform |
| Encryption in transit            | TLS 1.3 on all endpoints         | —        | Platform |

---

### Part B — Necessity and Proportionality (GDPR art. 35(7)(b))

#### B.1 Why each processing purpose is necessary

- **P-01 Detection**: Anomaly detection over observability data is the core mechanism
  for reducing MTTD. No less-intrusive technical alternative achieves comparable MTTD
  reduction — aggregate metrics alone miss individual-request-level anomalies.
- **P-02 Triage**: Severity classification requires service context and CUJ data, which
  may carry pseudonymised user identifiers. Alternative: manual triage — but this
  defeats the MTTR reduction objective (RQ2).
- **P-03 RCA**: Root cause analysis over logs and traces is the only automated path to
  identifying causal chains. Anonymised-only data would degrade RCA quality below the
  80% utility threshold (spec 22 / ADR-0031).
- **P-04 Remediation**: Production actions require the agent to know which service to
  target — service names are not personal data but co-appear with pseudonymised user IDs
  in logs.
- **P-05 Post-mortem**: Post-mortems use role labels (not names) — the minimal
  identifying information required for accountability.
- **P-06 Research**: Anonymised corpus is the legal basis; pseudonymised residual data
  is needed only where anonymisation degrades MTTD measurement precision below utility
  threshold.

#### B.2 Data minimisation measures

- OTel SpanProcessor masks PII at point of collection — data enters the pipeline
  already pseudonymised/masked (ADR-0014).
- Only the minimum prompt context is sent to the LLM — no full log dumps; only relevant
  excerpts (ADR-0028 §data minimisation).
- `user_id` is pseudonymised at source; the mapping table is in Vault, inaccessible to
  agents.
- Post-mortems use role labels; no real names are collected or stored by the Copilot.

---

### Part C — Risk Assessment (GDPR art. 35(7)(c), LGPD art. 38 II)

| Risk ID | Risk                                          | Likelihood | Impact   | Residual risk  | Mitigation                                                             |
| ------- | --------------------------------------------- | ---------- | -------- | -------------- | ---------------------------------------------------------------------- |
| R-01    | PII exposure via LLM prompt                   | Low        | High     | **Low**        | ADR-0028 Presidio sanitization; `sanitized=True` hard gate             |
| R-02    | PII in observability pipeline                 | Low        | High     | **Low**        | ADR-0014 OTel SpanProcessor + Loki pipeline defence-in-depth           |
| R-03    | Audit trail compromise (tampering)            | Very Low   | Critical | **Low**        | ADR-0024 GCS WORM + SHA-256 hash chain                                 |
| R-04    | Cross-border transfer without safeguards      | Very Low   | High     | **Low**        | ADR-0032 SCCs + LGPD art. 33 VI; PII stripped before transfer          |
| R-05    | Agent hallucination disclosing PII            | Low        | Medium   | **Low**        | ADR-0021 OWASP LLM06; Pydantic schema validation; confidence threshold |
| R-06    | Prompt injection leading to data exfiltration | Low        | High     | **Low**        | ADR-0021 OWASP LLM01; ADR-0028 sanitization; structured output         |
| R-07    | Unauthorised production action (HITL bypass)  | Very Low   | Critical | **Low**        | ADR-0023 ApprovalToken; Semgrep `hitl-bypass` rule; BLOCKED category   |
| R-08    | Data subject unable to exercise erasure right | Low        | Medium   | **Low**        | ADR-0030 + spec 20 §3.4 erasure procedure; 15-day SLA                  |
| R-09    | Novel PII pattern not caught by Presidio      | Medium     | Medium   | **Low–Medium** | Regex secondary pass (ADR-0028); residual risk accepted and monitored  |
| R-10    | Research corpus re-identification             | Low        | High     | **Low**        | ADR-0031 k-anonymity k≥5; re-ID risk < 5% gate before corpus use       |

No unmitigated High or Critical residual risks. R-09 is the only Medium residual risk,
accepted because: (a) regex secondary pass reduces the gap; (b) PII reaches no external
system (Anthropic API receives sanitized prompts only); (c) residual false-negatives
are documented in this register and monitored quarterly.

---

### Part D — Measures to Address Risks (GDPR art. 35(7)(d))

All technical controls listed in Part A §A.6 are operational. Evidence:

| Control                | Evidence                                                          | Phase   |
| ---------------------- | ----------------------------------------------------------------- | ------- |
| ADR-0014 OTel masking  | Unit test `tests/unit/test_otel_pii_masking.py`                   | Phase 5 |
| ADR-0028 Presidio gate | Unit test `tests/unit/test_pii_sanitizer.py`; Semgrep CI gate     | Phase 5 |
| ADR-0023 HITL gate     | Unit test `tests/unit/test_hitl_enforcement.py`; integration test | Phase 5 |
| ADR-0024 Audit trail   | Unit test `tests/unit/test_audit_chain.py`                        | Phase 5 |
| ADR-0031 k-anonymity   | Script `src/research/anonymization_pipeline.py`; ARX report       | Phase 5 |

Status "Phase 5" means controls are designed (ADRs and specs complete) but not yet
implemented. This DPIA must be re-validated after Phase 5 implementation to confirm
all controls are operational before production deployment.

---

### Part E — DPO Consultation Record (GDPR art. 35(2))

**DPO / Privacy Lead**: Valdomiro de Oliveira Souza Júnior
**Role**: Tech Lead, DPO, Privacy Lead, Dissertation Author — PPGCA/Unisinos
**Assessment scope**: Full system as described in specs 00–22
**Date of sign-off**: 2026-05-17
**Finding**: Processing is necessary for the research objectives (RQ1–RQ4). All
identified risks have documented mitigations. No unmitigated Critical or High residual
risks. Processing may proceed to production after Phase 5 controls are implemented and
validated.

**Condition**: This DPIA must be updated within 30 days of any material change to:
(a) data categories processed, (b) external recipients, (c) LLM provider or model,
or (d) agent autonomy boundaries.

---

### Part F — RIPD-Specific Fields (LGPD art. 38)

#### F.1 Description of processing and legal basis

Processing: Agentic AI Copilot for incident response — automated detection, triage,
root cause analysis, remediation proposal and post-mortem drafting over observability
data from cloud-native systems.

Legal basis per activity:

- Incident response operations (P-01–P-05): LGPD art. 7 IX (legitimate interest of
  the controller in providing reliable, fast incident response for cloud services)
- Research evaluation (P-06): LGPD art. 7 XIV + art. 23 (academic research — PPGCA/Unisinos dissertation)
- CPF processing (PII-05): LGPD art. 11 II (f) (regular exercise of rights) — incidental
  to log message content; masked before any further processing

#### F.2 Legitimate interest assessment (P-01–P-05)

- **Purpose test**: Reducing MTTD/MTTR in incident response is a legitimate operational
  interest; processing is not for marketing, profiling or discriminatory purposes.
- **Necessity test**: Automated processing of observability data containing user IDs and
  IP addresses is technically necessary — manual triage at the volume and velocity of
  cloud-native observability data is not feasible.
- **Balancing test**: Impact on data subjects is low because: (a) data is pseudonymised
  at source; (b) no decision affecting data subjects directly results from processing;
  (c) retention is limited to 90 days; (d) data subjects have erasure rights exercisable
  within 15 days.

#### F.3 Measures, safeguards and risk mitigation

All measures are documented in Part C (risk register) and Part D (evidence). Key
safeguards specific to LGPD:

- Brazilian PII categories (CPF, CNPJ, RG) handled by Presidio BR recognizers (ADR-0028)
- ANPD notification obligation: if a data breach occurs, notified within 2 business days
  per LGPD art. 48 (see `PRIVACY.md`)
- Data subject rights (art. 18): access, correction, deletion, portability — exercised
  via DPO email `valdomirojr@gmail.com`; response within 15 days

---

## 4. Acceptance Criteria

- [ ] All six parts (A–F) are authored with all required subsections
- [ ] `specs/privacy/19-pii-inventory.md` referenced and complete (Part A.2)
- [ ] All privacy ADRs (0027–0032) referenced as technical controls (Part A.6, Part D)
- [ ] Risk register (Part C): no unmitigated High or Critical residual risks
- [ ] DPO sign-off recorded with date and scope (Part E)
- [ ] LGPD-specific fields complete: legal basis, legitimate interest assessment, Brazilian PII (Part F)
- [ ] Completion checklist (ADR-0029) has no unchecked items
- [ ] `check_dpia_completeness.py` passes on this file (release gate)
- [ ] DPO / Privacy Lead + Legal review recorded before merge
- [ ] Language: English only (RULE-005)

### ADR-0029 completion checklist

- [x] All six sections (A–F) authored and internally consistent
- [x] PII inventory (`specs/privacy/19-pii-inventory.md`) referenced and complete
- [x] All privacy ADRs (0027–0032) referenced as technical controls
- [x] Risk register: no residual High risks without documented mitigation
- [x] DPO/Privacy Lead sign-off recorded with date and scope
- [ ] Legal review completed (waived: academic context; DPO = researcher; no external data subjects in research phase)
- [x] DPIA stored in `specs/privacy/21-dpia-ripd.md` and version-controlled

---

## 5. Linked ADRs

| ADR      | Relevance                                                                |
| -------- | ------------------------------------------------------------------------ |
| ADR-0014 | PII masking control — Part A.6, Part D evidence                          |
| ADR-0021 | OWASP LLM mitigations — R-05, R-06 risk mitigations                      |
| ADR-0023 | HITL gate — R-07 risk mitigation                                         |
| ADR-0024 | Audit trail — R-03 risk mitigation; Part D evidence                      |
| ADR-0027 | Privacy by Design — governs this DPIA lifecycle                          |
| ADR-0028 | PII sanitization — R-01, R-06, R-09 risk mitigations                     |
| ADR-0029 | DPIA/RIPD hard gate — defines this document's structure and release gate |
| ADR-0030 | Data retention — Part A.4 retention periods; R-08 mitigation             |
| ADR-0031 | Anonymization — R-10 mitigation; Part A.2 research corpus                |
| ADR-0032 | Cross-border transfers — Part A.5 recipients; R-04 mitigation            |

---

## References

- GDPR (EU 2016/679) Art. 35 — DPIA; Art. 35(7) — mandatory content
- LGPD (Lei 13.709/2018) Art. 38 — RIPD; Art. 7 IX/XIV; Art. 11; Art. 23; Art. 48
- EU AI Act (2024) Art. 9 — Risk management system
- ANPD Resolution CD/ANPD No. 2 (2022) — RIPD guidance
- ANPD Resolution CD/ANPD No. 19 (2024) — International transfer framework
- `specs/privacy/19-pii-inventory.md` — PII categories and data flows
- `specs/privacy/20-data-retention-policy.md` — retention schedule
- `specs/privacy/22-anonymization-standard.md` — research corpus anonymization (R-10)
- `PRIVACY.md` — public data processing notice
