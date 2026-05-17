# Skill: LGPD

**Domain**: privacy
**Activation triggers**: LGPD, ANPD, RIPD, DPO, Lei 13.709, Brazilian data protection, CPF, CNPJ, sensitive data Brazil, legitimate interest, data subject rights Brazil, ANPD notification, art. 48
**References**: specs/privacy/21-dpia-ripd.md, specs/privacy/19-pii-inventory.md, ADR-0027, ADR-0029

---

## LGPD Legal Basis Framework

| LGPD Article | Legal basis                       | Processing purposes                                 |
| ------------ | --------------------------------- | --------------------------------------------------- |
| Art. 7 IX    | Legitimate interest of controller | Incident response operations (P-01 to P-05)         |
| Art. 7 XIV   | Research / scientific study       | Dissertation evaluation corpus (P-06)               |
| Art. 11 II f | Regular exercise of rights        | CPF processing (PII-05) — incidental to log content |
| Art. 23      | Research cooperation              | Academic research — PPGCA/Unisinos                  |

### Legitimate Interest Assessment (Art. 7 IX)

- **Purpose test**: Reducing MTTD/MTTR is a legitimate operational interest — not marketing, profiling or discrimination.
- **Necessity test**: Automated processing of observability data with `user_id` and IP addresses is technically necessary; manual triage at cloud-native scale is not feasible.
- **Balancing test**: Low impact on data subjects because: (a) data is pseudonymised at source; (b) no decision directly affects data subjects; (c) retention is limited to 90 days; (d) erasure rights exercisable within 15 days.

---

## Brazilian PII Specifics

| PII      | LGPD classification       | Recognizer     | Replacement token |
| -------- | ------------------------- | -------------- | ----------------- |
| CPF      | Sensitive data (art. 11)  | `BR_CPF`       | `[MASKED_CPF]`    |
| CNPJ     | Personal data (art. 5 II) | `BR_CNPJ`      | `[MASKED_CNPJ]`   |
| Phone BR | Personal data             | Presidio phone | `[MASKED_PHONE]`  |

**CPF elevated requirements**: any processing of CPF requires legal basis under art. 11 (elevated tier). The Copilot processes CPF only as a masked token — Presidio BR recognizer fires at ingestion before any storage or LLM call.

---

## Data Subject Rights (Art. 18)

| Right                    | LGPD Article | Response deadline | Mechanism                                                    |
| ------------------------ | ------------ | ----------------- | ------------------------------------------------------------ |
| Access                   | Art. 18 I    | 15 days           | DPO queries audit trail + Loki; provides formatted report    |
| Correction               | Art. 18 III  | 15 days           | DPO corrects pseudonymised reference; logs erasure event     |
| Deletion (non-essential) | Art. 18 VI   | 15 days           | Erasure procedure (spec 20 §3.4)                             |
| Portability              | Art. 18 V    | 15 days           | DPO exports relevant records in JSON format                  |
| Information on sharing   | Art. 18 VII  | 15 days           | DPO consults ADR-0032 transfer register; responds in writing |
| Revocation of consent    | Art. 18 IX   | Immediate         | N/A — processing is under legitimate interest, not consent   |

Contact: DPO email `valdomirojr@gmail.com`

### Erasure Procedure (Art. 18 VI / Art. 16)

```
Step 1  DPO receives erasure request (email to valdomirojr@gmail.com)
Step 2  Verify identity of data subject (out-of-band confirmation)
Step 3  Identify user_id pseudonym(s) in Vault mapping table (never in repo)
Step 4  Delete or anonymise in each active data category:
        - Loki:   query by user_id label → delete matching log streams
        - Tempo:  query by user.id attribute → delete matching traces
        - Audit trail (GCS WORM): replace user_id with [DELETED] in-place;
          append erasure-log record to chain
        - Post-mortems: redact pseudonymised role label linked to user
Step 5  Generate deletion evidence report
Step 6  Respond in writing within 15 days
Step 7  Emit audit.subject_erasure_completed event
```

---

## ANPD Notification Obligation (Art. 48)

On any confirmed data breach involving personal data:

| Condition            | Deadline               | Action                                                          |
| -------------------- | ---------------------- | --------------------------------------------------------------- |
| Breach confirmed     | Within 2 business days | Notify ANPD and affected data subjects                          |
| Notification content | —                      | Nature of data, number of subjects, measures taken, DPO contact |
| Follow-up report     | As requested           | Full incident timeline, root cause, prevention measures         |

ANPD portal: [https://www.gov.br/anpd](https://www.gov.br/anpd)

Breach detection triggers: `audit.write_failed`, unexpected access pattern alerts, SIEM alerts (out of Copilot scope — escalate to security team).

---

## RIPD Structure (Art. 38)

The RIPD (Relatório de Impacto à Proteção de Dados Pessoais) is filed at `specs/privacy/21-dpia-ripd.md`. It must contain all six sections:

| Section | Content                                                             | LGPD reference |
| ------- | ------------------------------------------------------------------- | -------------- |
| A       | Processing description, purposes, legal basis                       | Art. 38 I      |
| B       | Necessity and proportionality assessment                            | Art. 38 II     |
| C       | Risk register with likelihood and impact                            | Art. 38 II     |
| D       | Technical and organisational measures                               | Art. 38 II     |
| E       | DPO consultation record with sign-off date                          | Art. 38 §1     |
| F       | LGPD-specific fields: legitimate interest assessment, Brazilian PII | Art. 38        |

**Hard gate**: No production deployment handling real incident data proceeds without RIPD complete and signed (CLAUDE.md §1.6 criterion 4, ADR-0029).

---

## RIPD Update Triggers

The RIPD (spec 21) must be updated within 30 days of any material change to:

- Data categories processed (new PII type added)
- External recipients (new third-party integration)
- LLM provider or model version
- Agent autonomy boundaries (new HITL/HOTL/BLOCKED classification)

---

## LGPD Compliance Checklist

For any PR that introduces new data processing or modifies existing processing:

- [ ] New processing purpose documented in RIPD Part A
- [ ] Legal basis identified (art. 7 IX / XIV / art. 11 II) — no undocumented processing
- [ ] Brazilian PII (CPF/CNPJ/phone) handled by Presidio BR recognizer
- [ ] Retention period set and TTL configured in infrastructure (spec 20)
- [ ] Data subject rights exercisable via DPO contact documented
- [ ] Cross-border transfer (if any) covered by ADR-0032 transfer register
- [ ] RIPD updated if this is a material change
- [ ] ANPD notification procedure covered in `PRIVACY.md`
