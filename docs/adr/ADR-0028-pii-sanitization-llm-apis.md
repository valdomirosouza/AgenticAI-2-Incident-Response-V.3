# ADR-0028: PII Sanitization Before Sending Data to External LLM APIs

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / DPO / Privacy Lead — researcher)
**Affected RQs**: RQ4 (privacy compliance), RQ3 (guardrails)

---

## Context

The Copilot sends prompts to the Anthropic Claude API (ADR-0003) containing:

- Log excerpts from the observability pipeline
- Distributed trace data
- Metric time series with labels
- Runbook content
- Post-mortem excerpts
- Structured incident context

Any of these inputs may contain PII — user IDs, IP addresses, email addresses in log
messages, names in post-mortems, CPF/CNPJ in request parameters. Sending raw PII
to an external API constitutes an international data transfer subject to:

- **LGPD art. 7** — processing must have a valid legal basis; sending PII to a third
  party (Anthropic) without explicit consent or contract requires documented legitimate
  interest and data transfer safeguards.
- **GDPR art. 6** — lawfulness of processing; transfer to a processor requires a DPA
  (Data Processing Agreement) and appropriate safeguards.
- **OWASP LLM06** (Sensitive Information Disclosure) — LLMs may inadvertently reproduce
  or expose PII present in the prompt in their output, logs or training pipelines.

CLAUDE.md §1.6 criterion 5 is a hard gate: _"Observability pipelines enforce PII masking
before ingestion into any third-party system."_ The LLM API is an external third-party
system; this ADR operationalises that gate specifically for LLM prompt construction.

## Decision

**No prompt is dispatched to any external LLM API without passing through the
PII sanitizer.** The sanitizer runs as a mandatory, synchronous step in the
`LLMPort` outbound adapter before the API call is made.

### Sanitization library and method

**Primary:** [**Microsoft Presidio**](https://github.com/microsoft/presidio) (v2.x)
— NLP-based PII detection and anonymization for Python.

**Secondary:** Regex-based rules for structured PII patterns (CPF, CNPJ, Brazilian
phone numbers, IP addresses) that Presidio may miss due to language model coverage.

### Presidio configuration

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

ENTITIES_TO_DETECT = [
    "EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS",
    "PERSON", "LOCATION", "CREDIT_CARD",
    "IBAN_CODE", "MEDICAL_LICENSE", "URL",
    "BR_CPF", "BR_CNPJ", "BR_RG",           # Brazilian recognizers
]

REPLACEMENT_MAP = {
    "EMAIL_ADDRESS":  "[MASKED_EMAIL]",
    "PHONE_NUMBER":   "[MASKED_PHONE]",
    "IP_ADDRESS":     "[MASKED_IP]",
    "PERSON":         "[MASKED_NAME]",
    "BR_CPF":         "[MASKED_CPF]",
    "BR_CNPJ":        "[MASKED_CNPJ]",
    # ... etc
}
```

Language support: `en` (English) and `pt` (Portuguese) — both enabled given the
research context (Brazilian operators, English runbooks).

### Sanitization pipeline per prompt

```
Raw prompt (may contain PII)
        │
        ▼
1. Presidio AnalyzerEngine — detect PII entities (NLP, score >= 0.7)
        │
        ▼
2. Regex pass — detect structured PII missed by Presidio
   (CPF pattern, IPv6, Brazilian phone formats)
        │
        ▼
3. AnonymizerEngine — replace detected entities with typed placeholders
        │
        ▼
4. Audit log — emit pii.masked event (ADR-0024) for each replaced entity:
   { event: "pii.masked", field: "prompt", entity_type: "BR_CPF",
     count: 1, trace_id: "...", span_id: "..." }
        │
        ▼
Sanitized prompt → Anthropic API call
```

### Hard gate enforcement in LLM adapter

The `LLMAdapter` (`src/adapters/outbound/llm_adapter.py`) enforces the gate:

```python
def complete(self, prompt: str, *, sanitized: bool = False) -> str:
    if not sanitized:
        raise PiiSanitizationRequired(
            "Prompt must be sanitized before LLM dispatch. "
            "Use pii_sanitizer.sanitize(prompt) and pass sanitized=True."
        )
    return self._client.messages.create(...)
```

Callers must explicitly pass `sanitized=True` after running the sanitizer. This
pattern prevents accidental bypass — the unsanitized path is not available by default.

The custom Semgrep rule `llm-unsanitized-prompt` (ADR-0017) detects any call to
`llm_adapter.complete()` without `sanitized=True` and blocks the PR gate.

### Confidence threshold

Presidio detections below score 0.7 are logged as warnings but not masked —
to avoid degrading prompt quality with over-aggressive false positives. The threshold
is configurable in `src/guardrails/pii_sanitizer_config.py`.

## Alternatives Considered

| Alternative                       | Pros                                                                                                         | Cons                                                                                            |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| **No sanitization**               | Zero latency overhead                                                                                        | LGPD art. 7 / GDPR art. 6 violated; OWASP LLM06 risk unmitigated; CLAUDE.md criterion 5 not met |
| **Regex-only sanitization**       | Fast; no ML dependency                                                                                       | Brazilian-Portuguese NLP patterns are too varied for regex-only; high false negative rate       |
| **Microsoft Presidio + regex** ✅ | NLP coverage for unstructured PII + regex for structured patterns; multilingual (en+pt); actively maintained | ~50–100ms latency per sanitization pass; Presidio adds an ML dependency                         |
| **Custom NLP model**              | Tuned for this domain                                                                                        | Training cost and maintenance burden disproportionate for a research prototype                  |

## Consequences

**Positive:**

- CLAUDE.md §1.6 criterion 5 satisfied for the LLM API path.
- OWASP LLM06 mitigated: PII stripped from prompt before it can be reproduced
  in LLM output or retained in provider logs.
- `PiiSanitizationRequired` exception makes bypass impossible by default —
  developers cannot accidentally skip sanitization.
- Presidio + Brazilian recognizers covers LGPD-specific PII categories (CPF, CNPJ, RG).

**Negative / Trade-offs:**

- ~50–100ms latency per LLM call for the sanitization pass — acceptable given
  MTTD target is minutes, not seconds.
- Presidio false negatives (novel PII patterns) are mitigated by the regex secondary
  pass but cannot be eliminated entirely — residual risk accepted and documented in DPIA/RIPD (ADR-0029).
- `sanitized=True` parameter is a convention, not a cryptographic proof — a developer
  could pass `sanitized=True` without running the sanitizer. Mitigated by the Semgrep
  custom rule that checks the call graph.

## Review Criteria

Revisit this decision if:

- Presidio is no longer maintained or its Brazilian recognizers degrade in accuracy.
- ANPD issues guidance that requires cryptographic proof of sanitization rather than
  an audit log entry.
- A new PII category is identified in the DPIA/RIPD (ADR-0029) — add the corresponding
  Presidio entity type and replacement rule.

## References

- LGPD (Lei 13.709/2018) Art. 7 — Legal bases for personal data processing
- GDPR (EU 2016/679) Art. 6 — Lawfulness of processing
- OWASP LLM Top 10 (2025) LLM06 — Sensitive Information Disclosure
- Microsoft Presidio v2 — github.com/microsoft/presidio
- `docs/adr/ADR-0003-llm-provider-model-selection.md` — LLM provider (Anthropic)
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md` — PII masking in observability (complementary)
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md` — pii.masked audit events
- `docs/adr/ADR-0032-cross-border-data-transfer-safeguards.md` — transfer safeguards for Anthropic API
- `specs/privacy/19-pii-inventory.md` — full PII inventory (to be authored, issue #14)
- CLAUDE.md §1.6 criterion 5 — PII masking hard gate
