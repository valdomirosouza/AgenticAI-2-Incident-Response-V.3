# Skill: GDPR

**Domain**: privacy
**Activation triggers**: GDPR, DPIA, data subject rights, right to erasure, right to access, cross-border transfers, SCCs, standard contractual clauses, EU data protection, GDPR art. 35, legitimate interest GDPR, special category data
**References**: specs/privacy/21-dpia-ripd.md, specs/privacy/19-pii-inventory.md, ADR-0029, ADR-0032

---

## GDPR Legal Basis

| Processing purpose            | Agent(s)                       | GDPR legal basis                   |
| ----------------------------- | ------------------------------ | ---------------------------------- |
| P-01: Anomaly detection       | DetectionAgent                 | Art. 6(1)(f) — legitimate interest |
| P-02: Severity + notification | TriageAgent                    | Art. 6(1)(f) — legitimate interest |
| P-03: Root cause analysis     | RCAAgent                       | Art. 6(1)(f) — legitimate interest |
| P-04: Remediation (HITL)      | RemediationAgent               | Art. 6(1)(f) — legitimate interest |
| P-05: Post-mortem drafting    | PostMortemAgent                | Art. 6(1)(f) — legitimate interest |
| P-06: Research evaluation     | All agents (anonymised corpus) | Art. 89 — research exemption       |
| CPF processing (special cat.) | All observability pipelines    | Art. 9(2)(f) — legal claim         |

---

## DPIA Requirements (Art. 35)

A DPIA is **mandatory** for this system because it:

- Processes personal data at scale using new technology (AI/ML)
- Involves systematic profiling-adjacent operations (anomaly detection)
- Uses automated processing that produces outputs that inform human decisions

The DPIA is filed at `specs/privacy/21-dpia-ripd.md` and covers all six mandatory sections per Art. 35(7):

| Art. 35(7) | Section | Content                                          |
| ---------- | ------- | ------------------------------------------------ |
| (a)        | Part A  | Description of processing, purposes, legal bases |
| (b)        | Part B  | Necessity and proportionality                    |
| (c)        | Part C  | Risk register (10 identified risks)              |
| (d)        | Part D  | Technical and organisational measures            |
| Art. 35(2) | Part E  | DPO consultation record + sign-off               |
| —          | Part F  | LGPD/RIPD-specific fields                        |

**Hard gate**: No production deployment with real incident data proceeds without a complete and signed DPIA (CLAUDE.md §1.6 criterion 4, ADR-0029).

---

## Risk Register Summary (DPIA Part C)

| Risk ID | Risk                                          | Residual risk  | Key mitigation                                         |
| ------- | --------------------------------------------- | -------------- | ------------------------------------------------------ |
| R-01    | PII exposure via LLM prompt                   | **Low**        | Presidio sanitization + `sanitized=True` gate          |
| R-02    | PII in observability pipeline                 | **Low**        | OTel SpanProcessor + Loki defence-in-depth             |
| R-03    | Audit trail tampering                         | **Low**        | GCS WORM + SHA-256 hash chain                          |
| R-04    | Cross-border transfer without safeguards      | **Low**        | SCCs + LGPD art. 33 VI; PII stripped before transfer   |
| R-05    | Hallucination disclosing PII                  | **Low**        | OWASP LLM06; Pydantic schema; confidence threshold     |
| R-06    | Prompt injection → data exfiltration          | **Low**        | OWASP LLM01; ADR-0028 sanitization; structured output  |
| R-07    | Unauthorised production action (HITL bypass)  | **Low**        | ApprovalToken; Semgrep `hitl-bypass`; BLOCKED category |
| R-08    | Data subject unable to exercise erasure right | **Low**        | Erasure procedure (spec 20 §3.4); 15-day SLA           |
| R-09    | Novel PII not caught by Presidio              | **Low–Medium** | Regex secondary pass; no PII reaches external systems  |
| R-10    | Research corpus re-identification             | **Low**        | k-anonymity k ≥ 5; re-ID risk < 5% gate (spec 22)      |

No unmitigated High or Critical residual risks.

---

## Cross-Border Transfers (Art. 46, ADR-0032)

| Recipient        | Country | Data category                           | Safeguard                       |
| ---------------- | ------- | --------------------------------------- | ------------------------------- |
| Anthropic Claude | USA     | Sanitized prompts (no PII per ADR-0028) | SCCs Module 1 + LGPD art. 33 VI |
| GitHub Actions   | USA     | Source code, CI logs (no PII, RULE-C03) | SCCs Module 1 + GitHub DPA      |
| GCS (audit)      | EU/US   | Pseudonymised audit records             | SCCs if non-EU; adequacy if EU  |

**Key invariant**: No raw PII crosses the EU/Brazil border — Anthropic API receives only sanitized prompts. This eliminates the primary Art. 46 risk.

---

## Data Subject Rights (GDPR)

| Right                             | Article | Deadline  | Mechanism                                                 |
| --------------------------------- | ------- | --------- | --------------------------------------------------------- |
| Access                            | Art. 15 | 30 days   | DPO queries audit trail + Loki; exports formatted report  |
| Rectification                     | Art. 16 | 30 days   | DPO corrects pseudonymised reference in applicable stores |
| Erasure ("right to be forgotten") | Art. 17 | 30 days   | Erasure procedure — see spec 20 §3.4                      |
| Restriction                       | Art. 18 | 30 days   | DPO suspends automated processing for the data subject    |
| Portability                       | Art. 20 | 30 days   | DPO exports records in JSON; machine-readable format      |
| Objection                         | Art. 21 | Immediate | DPO assesses compelling grounds; documents outcome        |

Contact: DPO `valdomirojr@gmail.com`

### Erasure and WORM Constraint

Audit trail records are stored in GCS with WORM Object Lock — deletion is architecturally impossible. For erasure requests:

1. `user_id` reference in audit record `payload` is replaced with `[DELETED]` in-place
2. `record_hash` is recomputed and flagged `[REDACTED_FOR_ERASURE]`
3. A companion erasure-log record is appended to the hash chain
4. Hash chain integrity is preserved — only the personal data reference is removed

---

## DPIA Update Triggers

The DPIA (spec 21) must be updated within 30 days of any material change to:

- Data categories processed
- External recipients
- LLM provider or model (ADR-0003 update triggers DPIA update)
- Agent autonomy boundaries (new HITL/HOTL/BLOCKED type)

---

## GDPR Compliance Checklist

For any PR introducing or modifying personal data processing:

- [ ] Processing purpose has identified GDPR legal basis (Art. 6 or Art. 9)
- [ ] DPIA Part A updated if new data category or purpose added
- [ ] No special category data (Art. 9) processed without Art. 9(2) basis
- [ ] Cross-border transfer: new external recipient registered in ADR-0032 transfer log
- [ ] Retention period configured per spec 20 — no indefinite retention
- [ ] Data subject rights exercisable for any new data category
- [ ] DPIA Part C risk register updated if new risk introduced
- [ ] DPIA re-validated if this constitutes a material change
