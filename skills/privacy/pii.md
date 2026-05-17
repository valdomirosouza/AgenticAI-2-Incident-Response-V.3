# Skill: PII

**Domain**: privacy
**Activation triggers**: PII, personal data, Presidio, PII masking, PII classification, user_id, IP address, CPF, CNPJ, email, sanitization, pii_sanitizer, sanitized=True
**References**: specs/privacy/19-pii-inventory.md, ADR-0014, ADR-0028

---

## PII Categories Processed

| ID     | PII type                    | LGPD classification       | GDPR classification      | Where it appears                                  | Sensitivity |
| ------ | --------------------------- | ------------------------- | ------------------------ | ------------------------------------------------- | ----------- |
| PII-01 | `user_id` (opaque token)    | Personal data (art. 5 II) | Personal data (art. 4)   | Logs, traces, incident records                    | Medium      |
| PII-02 | IP address                  | Personal data             | Personal data            | HTTP access logs, OTel spans                      | Medium      |
| PII-03 | Email address               | Personal data             | Personal data            | On-call notification metadata, post-mortem drafts | Medium      |
| PII-04 | Person name                 | Personal data             | Personal data            | Post-mortem drafts (if not pseudonymised)         | Medium      |
| PII-05 | CPF                         | **Sensitive** (art. 11)   | Personal data            | Request parameters in log messages                | **High**    |
| PII-06 | CNPJ                        | Personal data             | Personal data            | Request parameters in log messages                | Medium      |
| PII-07 | Brazilian phone number      | Personal data             | Personal data            | Request parameters, on-call metadata              | Medium      |
| PII-08 | Request path + query string | Quasi-identifier          | Personal data (indirect) | HTTP access logs                                  | Low–Medium  |
| PII-09 | Stack trace content         | Quasi-identifier          | Personal data (indirect) | Error logs                                        | Medium      |
| PII-10 | Service account roles       | Non-personal              | Non-personal             | Audit trail (`agent_role` pseudonymised)          | Low         |

**PII-05 CPF is a sensitive category** under LGPD art. 11 — requires elevated legal basis (LGPD art. 11 II(f) + art. 7 IX). Processed only as a masked token `[MASKED_CPF]` after the Presidio BR recognizer fires.

---

## Masking Rules — Logs (Loki)

| PII category        | Masking rule                            | Layer                | ADR                |
| ------------------- | --------------------------------------- | -------------------- | ------------------ |
| PII-01 `user_id`    | Replace with `usr_<sha256_8chars>`      | OTel SpanProcessor   | ADR-0014           |
| PII-02 IP address   | Replace with `10.x.x.0/24` subnet       | OTel SpanProcessor   | ADR-0014           |
| PII-03 Email        | Replace with `[MASKED_EMAIL]`           | Presidio + OTel      | ADR-0014, ADR-0028 |
| PII-04 Name         | Replace with `[MASKED_NAME]`            | Presidio             | ADR-0028           |
| PII-05 CPF          | Replace with `[MASKED_CPF]`             | Presidio BR          | ADR-0028           |
| PII-06 CNPJ         | Replace with `[MASKED_CNPJ]`            | Presidio BR          | ADR-0028           |
| PII-07 Phone        | Replace with `[MASKED_PHONE]`           | Presidio             | ADR-0028           |
| PII-08 Query string | Strip known PII keys from URL           | OTel HTTP middleware | ADR-0014           |
| PII-09 Stack trace  | Presidio scan; redact detected entities | Presidio             | ADR-0028           |

## Masking Rules — Distributed Traces (Tempo)

| PII category     | Masking rule                                          | Layer              | ADR      |
| ---------------- | ----------------------------------------------------- | ------------------ | -------- |
| PII-01 `user_id` | Replace with `usr_<hash>` in `user.id` span attribute | OTel SpanProcessor | ADR-0014 |
| PII-02 IP        | Not stored in span attributes (excluded)              | OTel SpanProcessor | ADR-0014 |
| PII-03–07        | Presidio scan on any free-text attributes             | OTel SpanProcessor | ADR-0014 |
| Raw prompt       | **Never stored in spans** (`llm.prompt` excluded)     | By design          | ADR-0030 |

## Masking Rules — LLM Prompts (Anthropic API)

| PII category  | Masking rule                                                         | Tool         | ADR      |
| ------------- | -------------------------------------------------------------------- | ------------ | -------- |
| All PII-01–07 | Presidio AnalyzerEngine (score ≥ 0.7) → AnonymizerEngine replacement | Presidio v2  | ADR-0028 |
| PII-05 CPF    | `BR_CPF` recognizer → `[MASKED_CPF]`                                 | Presidio BR  | ADR-0028 |
| PII-06 CNPJ   | `BR_CNPJ` recognizer → `[MASKED_CNPJ]`                               | Presidio BR  | ADR-0028 |
| Residual      | Regex secondary pass (IPv6, phone formats)                           | Custom regex | ADR-0028 |

Prompts are **never persisted** after the API call (ADR-0030).

---

## Presidio Sanitization Pattern

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def sanitize(text: str, language: str = "pt") -> str:
    results = analyzer.analyze(
        text=text,
        language=language,
        score_threshold=0.7,
        entities=[
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS",
            "URL", "BR_CPF", "BR_CNPJ",
        ],
    )
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text

# REQUIRED pattern — sanitize then pass sanitized=True
sanitized_excerpt = sanitize(log_excerpt[:2000])
result = llm_adapter.complete(sanitized_excerpt, sanitized=True)
```

**Hard gate**: `LLMAdapter.complete()` raises `PiiSanitizationRequired` if `sanitized=True` is not passed. Enforced by Semgrep rule `llm-unsanitized-prompt` (gate G06).

---

## Data Flow Diagram

```
                ┌─────────────────────────────────────────────────┐
                │         TRUST BOUNDARY: Kubernetes cluster       │
                │                                                  │
 User request  ─►  API Layer ──► OrchestratorAgent                │
 (may contain    │      │               │                          │
  PII)           │      │ OTel SDK       │ PII stripped             │
                 │      │ SpanProcessor  │ (ADR-0028 Presidio)      │
                 │      │ (ADR-0014)     │                          │
                 │      ▼               ▼                          │
                 │ ┌─────────┐   ┌─────────────┐                  │
                 │ │ Logs    │   │ LLM Adapter │                  │
                 │ │ (masked)│   │(sanitized   │                  │
                 │ └────┬────┘   │ prompt only)│                  │
                 │      │        └──────┬───────┘                  │
                 │      │               │ no PII crosses boundary  │
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

---

## Legal Basis

| PII category     | LGPD legal basis                                    | GDPR legal basis                   |
| ---------------- | --------------------------------------------------- | ---------------------------------- |
| PII-01–04, 06–09 | Art. 7 IX (legitimate interest — incident response) | Art. 6(1)(f) (legitimate interest) |
| PII-05 CPF       | Art. 11 II (f) + Art. 7 IX                          | Art. 9(2)(f) special category      |
| Research corpus  | Art. 7 XIV + Art. 23 (research cooperation)         | Art. 89 (research exemption)       |

---

## PII Checklist for Code Review

- [ ] `pii_sanitizer.sanitize()` called before any LLM prompt construction
- [ ] `sanitized=True` passed to `llm_adapter.complete()`
- [ ] No PII in span attributes — check forbidden fields list (spec 10)
- [ ] No email, name, or CPF in structured log fields
- [ ] Stack traces run through Presidio before logging
- [ ] No PII in any repository file (RULE-C03)
