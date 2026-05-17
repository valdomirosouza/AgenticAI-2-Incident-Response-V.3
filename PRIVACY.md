# Privacy and Data Processing Notice

> This notice applies to the **Agentic AI Copilot for Incident Response** research project.
> It covers the processing of personal data in the context of a Master's dissertation at PPGCA / Unisinos.
> Governed by LGPD (Lei 13.709/2018) and GDPR (EU 2016/679).

---

## Data Controller

**Name:** Valdomiro de Oliveira Souza Júnior
**Institution:** PPGCA / Unisinos — Programa de Pós-Graduação em Computação Aplicada
**Contact:** valdomirojr@gmail.com
**Role:** Researcher / Data Controller

## Purpose of Processing

Personal data may be processed for the following research purposes:

| Purpose                                                          | Legal basis (LGPD)                                     | Legal basis (GDPR)                |
| ---------------------------------------------------------------- | ------------------------------------------------------ | --------------------------------- |
| Academic research on incident response patterns                  | Art. 7, XIV (legitimate interest) + Art. 23 (research) | Art. 6(1)(f) legitimate interests |
| Evaluation of AI-assisted incident detection and triage          | Art. 7, IX (legitimate interest)                       | Art. 6(1)(f) legitimate interests |
| Testing observability pipelines with anonymized operational data | Art. 7, II (research)                                  | Art. 89 (research exemption)      |

**No** personal data is collected from end users for commercial purposes.

## Categories of Personal Data

| Category                    | Examples                                            | Applies to                              |
| --------------------------- | --------------------------------------------------- | --------------------------------------- |
| **Operational identifiers** | `user_id`, IP address, device ID in system logs     | Log and trace fixtures used in research |
| **Incident metadata**       | Engineer names in post-mortems, on-call assignments | Research corpus (anonymized before use) |

All personal data used in research fixtures is **anonymized or pseudonymized** before ingestion into any analysis pipeline, following the anonymization standard (to be detailed in `specs/privacy/22-anonymization-standard.md`).

## PII in Observability Pipelines

In accordance with **ADR-0014** (to be authored in Phase 1), the system enforces:

- **Mandatory PII masking** in all log lines and distributed traces before ingestion into observability backends
- **Sanitization** of PII fields before any data is sent to external LLM APIs (ADR-0028)
- **Zero PII** in test fixtures, CI artifacts or repository files (RULE-C03)

## Data Retention

| Data category                  | Retention period                       | Deletion procedure                    |
| ------------------------------ | -------------------------------------- | ------------------------------------- |
| Research corpus fixtures       | Duration of dissertation + 5 years     | Secure deletion upon project archival |
| Anonymized incident datasets   | Duration of dissertation               | Deleted after thesis defense          |
| System logs (when operational) | 30 days (hot) / 90 days (cold archive) | Automated TTL deletion                |
| Audit trail records            | Minimum 2 years                        | Per data retention policy (ADR-0030)  |

## Data Subject Rights

Under LGPD (arts. 17–22) and GDPR (arts. 15–22), data subjects have the right to:

- **Access** — request confirmation of processing and a copy of data held
- **Correction** — request correction of inaccurate or incomplete data
- **Deletion** — request erasure where there is no legal basis to retain
- **Portability** — receive data in a structured, machine-readable format
- **Revocation of consent** — where processing is based on consent
- **Information** — be informed about third parties with whom data has been shared

To exercise any of these rights, contact: **valdomirojr@gmail.com**
Response within **15 days** as required by LGPD art. 19.

## International Data Transfers

When this project uses external LLM APIs (e.g. Anthropic Claude), data sent to those APIs:

- Is **sanitized of PII** before transmission (ADR-0028)
- Is subject to the provider's own data processing terms
- Cross-border transfer safeguards will be documented in `docs/adr/ADR-0032-cross-border-data-transfer-safeguards.md` (Phase 1)

## Security Incident Notification

In the event of a personal data breach, notification will be provided:

- **ANPD** (Autoridade Nacional de Proteção de Dados): within **72 hours** of awareness — LGPD art. 48
- **Supervisory authority** (if EU data subjects are involved): within **72 hours** — GDPR art. 33
- **Affected data subjects**: without undue delay when high risk to rights and freedoms — GDPR art. 34

To report a potential data breach: **valdomirojr@gmail.com** with subject `[PRIVACY BREACH]`

## Data Protection Impact Assessment (DPIA / RIPD)

A formal DPIA (GDPR art. 35) and RIPD (LGPD art. 38) will be completed before any production deployment of Agentic AI features that process personal data. This is a hard gate per **ADR-0029** and CLAUDE.md §1.6 Success Criterion 4.

The assessment will be documented in `specs/privacy/21-dpia-ripd.md` (Phase 2, issue #14).

## Changes to This Notice

This notice will be updated when:

- New categories of personal data are processed
- The purpose of processing changes
- A new third-party processor is engaged
- Applicable law changes

All changes will be recorded in `CHANGELOG.md` under the `Security` or `Changed` category.

---

_Last updated: 2026-05-17 | Governed by ADR-0027 (Privacy by Design) and ADR-0029 (DPIA/RIPD) — to be authored in Phase 1._
