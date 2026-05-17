# Spec 19: PII Inventory

**Domain**: privacy
**Owner**: DPO / Privacy Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #14
**Linked ADRs**: ADR-0027, ADR-0028
**Review cadence**: Before every production deploy with PII changes; DPO + Legal required

---

## 1. Purpose

Provide the authoritative inventory of all PII categories processed by the Copilot,
a Data Flow Diagram showing every service that touches PII, and the masking rule
applied at each point of contact.

---

## 2. Context

ADR-0027 (Privacy by Design) requires a Privacy Impact section in every spec. ADR-0028
requires Presidio sanitization before every LLM prompt. CLAUDE.md §1.6 criterion 5
requires PII masking before ingestion into any third-party system. This spec is the
prerequisite for the DPIA/RIPD (spec 21) — the impact assessment references this
inventory as its data category register.

---

## 3. Decision

### 3.1 PII categories processed

| Category ID | PII type                    | LGPD classification                 | GDPR classification      | Where it appears                                  | Sensitivity |
| ----------- | --------------------------- | ----------------------------------- | ------------------------ | ------------------------------------------------- | ----------- |
| PII-01      | `user_id` (opaque token)    | Personal data (art. 5 II)           | Personal data (art. 4)   | Logs, traces, incident records                    | Medium      |
| PII-02      | IP address                  | Personal data                       | Personal data            | HTTP access logs, OTel spans                      | Medium      |
| PII-03      | Email address               | Personal data                       | Personal data            | On-call notification metadata, post-mortem drafts | Medium      |
| PII-04      | Person name                 | Personal data                       | Personal data            | Post-mortem drafts (if not pseudonymised)         | Medium      |
| PII-05      | CPF                         | Personal data (sensitive — art. 11) | Personal data            | Request parameters in log messages                | **High**    |
| PII-06      | CNPJ                        | Personal data                       | Personal data            | Request parameters in log messages                | Medium      |
| PII-07      | Brazilian phone number      | Personal data                       | Personal data            | Request parameters, on-call metadata              | Medium      |
| PII-08      | Request path + query string | Quasi-identifier                    | Personal data (indirect) | HTTP access logs                                  | Low–Medium  |
| PII-09      | Stack trace content         | Quasi-identifier                    | Personal data (indirect) | Error logs                                        | Medium      |
| PII-10      | Service account roles       | Non-personal                        | Non-personal             | Audit trail (`agent_role` pseudonymised)          | Low         |

PII-05 (CPF) is a **sensitive category** under LGPD art. 11 (equivalent to GDPR special
category data under art. 9). Any processing of CPF requires the elevated legal basis
documented in spec 21 (DPIA/RIPD).

### 3.2 Data Flow Diagram

```
                    ┌─────────────────────────────────────────────────┐
                    │         TRUST BOUNDARY: Kubernetes cluster       │
                    │                                                  │
 User request  ────►│ API Layer ──► OrchestratorAgent                 │
 (may contain PII)  │      │               │                          │
                    │      │ OTel SDK       │ PII stripped             │
                    │      │ SpanProcessor  │ (ADR-0028 Presidio)      │
                    │      │ (ADR-0014)     │                          │
                    │      ▼               ▼                          │
                    │ ┌─────────┐   ┌─────────────┐                  │
                    │ │ Logs    │   │ LLM Adapter │                  │
                    │ │ (masked)│   │(sanitized   │                  │
                    │ └────┬────┘   │ prompt only)│                  │
                    │      │        └──────┬───────┘                  │
                    │      │               │ no PII                   │
                    │      ▼               ▼                          │
                    │ ┌─────────┐   ┌──────────────────┐             │
                    │ │  Loki   │   │ Anthropic Claude │ (external)  │
                    │ │ (TTL 90d│   │  API  (USA)      │             │
                    │ └────┬────┘   └──────────────────┘             │
                    │      │                                          │
                    │ ┌────▼──────────────────────────────┐          │
                    │ │ Audit Trail (pseudonymised roles)  │          │
                    │ │ GCS Object Lock (TTL 2yr)          │          │
                    │ └───────────────────────────────────┘          │
                    └─────────────────────────────────────────────────┘
```

### 3.3 PII masking rules per pipeline

#### Logs (Loki)

| PII category        | Masking rule                            | Layer                    | ADR                |
| ------------------- | --------------------------------------- | ------------------------ | ------------------ |
| PII-01 `user_id`    | Replace with `usr_<sha256_8chars>`      | OTel SpanProcessor       | ADR-0014           |
| PII-02 IP address   | Replace with `10.x.x.0/24` subnet       | OTel SpanProcessor       | ADR-0014           |
| PII-03 Email        | Replace with `[MASKED_EMAIL]`           | Presidio + OTel          | ADR-0014, ADR-0028 |
| PII-04 Name         | Replace with `[MASKED_NAME]`            | Presidio                 | ADR-0028           |
| PII-05 CPF          | Replace with `[MASKED_CPF]`             | Presidio (BR recognizer) | ADR-0028           |
| PII-06 CNPJ         | Replace with `[MASKED_CNPJ]`            | Presidio (BR recognizer) | ADR-0028           |
| PII-07 Phone        | Replace with `[MASKED_PHONE]`           | Presidio                 | ADR-0028           |
| PII-08 Query string | Strip known PII keys from URL           | OTel HTTP middleware     | ADR-0014           |
| PII-09 Stack trace  | Presidio scan; redact detected entities | Presidio                 | ADR-0028           |

#### Distributed traces (Tempo)

| PII category     | Masking rule                                          | Layer              | ADR      |
| ---------------- | ----------------------------------------------------- | ------------------ | -------- |
| PII-01 `user_id` | Replace with `usr_<hash>` in `user.id` span attribute | OTel SpanProcessor | ADR-0014 |
| PII-02 IP        | Not stored in span attributes (excluded)              | OTel SpanProcessor | ADR-0014 |
| PII-03–07        | Presidio scan on any free-text attributes             | OTel SpanProcessor | ADR-0014 |
| Raw prompt       | **Never stored in spans** (`llm.prompt` excluded)     | By design          | ADR-0030 |

#### LLM prompts (Anthropic API)

| PII category  | Masking rule                                                         | Tool         | ADR      |
| ------------- | -------------------------------------------------------------------- | ------------ | -------- |
| All PII-01–07 | Presidio AnalyzerEngine (score ≥ 0.7) → AnonymizerEngine replacement | Presidio v2  | ADR-0028 |
| PII-05 CPF    | `BR_CPF` recognizer → `[MASKED_CPF]`                                 | Presidio BR  | ADR-0028 |
| PII-06 CNPJ   | `BR_CNPJ` recognizer → `[MASKED_CNPJ]`                               | Presidio BR  | ADR-0028 |
| Residual      | Regex secondary pass (IPv6, phone formats)                           | Custom regex | ADR-0028 |

Prompts are **never persisted** after the API call (ADR-0030).

#### Audit trail

All audit events use pseudonymised role labels (e.g. `engineer_alpha`) — no real
engineer names, email addresses or employee IDs. See spec 17 for the audit schema.

### 3.4 Legal basis per PII category

| PII category     | LGPD legal basis                                        | GDPR legal basis                   |
| ---------------- | ------------------------------------------------------- | ---------------------------------- |
| PII-01–04, 06–09 | Art. 7 IX (legitimate interest — incident response)     | Art. 6(1)(f) (legitimate interest) |
| PII-05 CPF       | Art. 11 II (f) (regular exercise of rights) + Art. 7 IX | Art. 9(2)(f) special category      |
| Research corpus  | Art. 7 XIV + Art. 23 (research cooperation)             | Art. 89 (research exemption)       |

---

## 4. Acceptance Criteria

- [ ] PII categories table covers all 10 categories (PII-01 to PII-10) with LGPD and GDPR classifications
- [ ] PII-05 CPF marked as sensitive/special category with elevated legal basis
- [ ] Data Flow Diagram shows all services that touch PII: API, OTel, Loki, LLM Adapter, Anthropic, Audit Trail
- [ ] Masking rules defined for all 3 pipelines: logs, traces, LLM prompts
- [ ] Raw prompt stored nowhere — "never persisted" statement present
- [ ] Legal basis table covers all PII categories including research corpus
- [ ] DPO / Privacy Lead + Legal review recorded before merge
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                                             |
| -------- | ------------------------------------------------------------------------------------- |
| ADR-0014 | PII masking in observability — OTel SpanProcessor masking rules                       |
| ADR-0027 | Privacy by Design — PII inventory required in every spec                              |
| ADR-0028 | PII sanitization — Presidio configuration and replacement map                         |
| ADR-0029 | DPIA/RIPD — references this inventory as the data category register                   |
| ADR-0030 | Data retention — LLM prompts never persisted; retention TTLs                          |
| ADR-0032 | Cross-border transfers — PII categories that cross to Anthropic (none, after masking) |

---

## References

- LGPD (Lei 13.709/2018) Art. 5 II, Art. 7 IX/XIV, Art. 11, Art. 23
- GDPR (EU 2016/679) Art. 4, Art. 6(1)(f), Art. 9(2)(f), Art. 89
- `docs/adr/ADR-0028-pii-sanitization-llm-apis.md`
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md`
- `specs/privacy/21-dpia-ripd.md` — DPIA references this inventory
- `specs/observability/09-logging-schema.md` — log field masking rules
- `specs/observability/10-tracing-schema.md` — span attribute masking rules
