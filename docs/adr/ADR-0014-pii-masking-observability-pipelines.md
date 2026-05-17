# ADR-0014: PII Masking in All Logs and Traces Before Ingestion

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher — acting as Privacy Lead)
**Affected RQs**: RQ4 (privacy compliance, LGPD/GDPR)

---

## Context

The observability pipeline ingests logs, metrics and traces from all agent services.
These signals may contain personal data if instrumentation is careless:

- Log lines may capture user-facing request parameters (names, emails, IDs).
- Distributed traces may capture HTTP headers, query strings or request bodies
  containing PII passed by end users.
- Metrics labels may include user-identifying dimensions.

Two legal obligations mandate masking before ingestion:

- **LGPD art. 46** — requires that personal data be protected by technical measures
  against unauthorised access, accidental or unlawful destruction or loss.
- **GDPR art. 5(1)(f)** (integrity and confidentiality) — personal data must be
  processed with appropriate security, including protection against unauthorised
  processing.

Additionally, CLAUDE.md §1.6 criterion 5 is a hard project gate: _"Observability
pipelines enforce PII masking before ingestion into any third-party system."_ This
criterion must pass before any production release.

External systems that receive telemetry (Anthropic LLM API, cloud logging backends)
are subject to cross-border transfer rules (ADR-0032) and must receive only
pseudonymised or anonymised data.

**Privacy Lead review:** This ADR was authored and reviewed by the researcher acting
in the Privacy Lead role. A formal DPIA/RIPD (ADR-0029) covers the broader data
processing assessment before production deployment.

## Decision

All observability data (logs, traces, metric labels) must be **masked of PII before
ingestion** into any observability backend or external API. Masking is applied at two
enforcement points:

### Enforcement point 1 — Application layer (OTel SDK)

The `PiiSanitizer` component (`src/guardrails/pii_sanitizer.py`) is invoked as an
**OTel SpanProcessor** and **log handler** before any telemetry leaves the application
process. It intercepts all spans and log records and applies masking rules.

```
Application code
     │ emits span / log
     ▼
PiiSanitizer (OTel SpanProcessor + logging.Filter)
     │ masks PII fields in-process
     ▼
OTel Collector (no PII reaches the network layer)
```

### Enforcement point 2 — OTel Collector pipeline

The OTel Collector applies a second-pass `attributes/pii-mask` processor as a
defence-in-depth measure. Any PII that escaped application-layer masking is masked
before export to the backend.

### Masking rules

| PII category           | Field patterns                                       | Masking action                                |
| ---------------------- | ---------------------------------------------------- | --------------------------------------------- |
| Email address          | `.*email.*`, `.*mail.*`                              | Replace with `[MASKED_EMAIL]`                 |
| Full name              | `.*name.*`, `.*user.*name.*`                         | Replace with `[MASKED_NAME]`                  |
| IP address (IPv4/IPv6) | Any field matching IP regex                          | Replace with `[MASKED_IP]`                    |
| Phone number           | `.*phone.*`, `.*tel.*`                               | Replace with `[MASKED_PHONE]`                 |
| Brazilian CPF/CNPJ     | CPF regex `\d{3}\.\d{3}\.\d{3}-\d{2}`                | Replace with `[MASKED_CPF]`                   |
| Auth tokens / API keys | `.*token.*`, `.*key.*`, `.*secret.*`, `.*password.*` | Replace with `[MASKED_SECRET]`                |
| `user_id` field        | `user_id`                                            | Keep as opaque pseudonymised ID — do NOT mask |

`user_id` is retained as an opaque pseudonymised identifier (not a direct identifier)
to allow incident correlation without exposing the real identity. The mapping between
`user_id` and the real user is stored only in the authoritative user service, not in
the observability backend.

### LLM API gate

Before any prompt is dispatched to the Anthropic API (ADR-0003), the `PiiSanitizer`
runs a full masking pass on the prompt content. This is a **hard gate** — the LLM
adapter (`src/adapters/outbound/llm_adapter.py`) will raise `PiiSanitizationRequired`
if the sanitizer has not been applied. This satisfies CLAUDE.md §1.6 criterion 5.

### Audit of masking actions

Every masking action is logged as a structured event:

```json
{
  "event": "pii.masked",
  "field": "email",
  "action": "replaced",
  "trace_id": "...",
  "span_id": "..."
}
```

This audit log is retained for 2 years (ADR-0030 data retention policy).

## Alternatives Considered

| Alternative                                           | Pros                                                                                                      | Cons                                                                            |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **No masking (rely on access controls)**              | Zero implementation cost                                                                                  | LGPD art. 46 / GDPR art. 5(1)(f) violated; any log exfiltration exposes raw PII |
| **Masking only at Collector (network layer)**         | Application code unchanged                                                                                | PII exists in memory and local OTel SDK buffers between emit and Collector      |
| **Full anonymisation (irreversible)**                 | No re-identification risk                                                                                 | `user_id` cannot be used for incident correlation without mapping table         |
| **Application-layer + Collector defence-in-depth** ✅ | Two enforcement points; PII never leaves application process unmasked; `user_id` retained for correlation | `PiiSanitizer` adds ~50ms latency per LLM call — acceptable given MTTD budget   |

## Consequences

**Positive:**

- CLAUDE.md §1.6 criterion 5 satisfied: PII masking enforced before any third-party
  ingestion — both observability backends and LLM API.
- LGPD art. 46 and GDPR art. 5(1)(f) compliance: technical measure implemented and
  documented in an auditable ADR.
- Masking audit log provides evidence trail for DPIA/RIPD (ADR-0029) and any future
  supervisory authority inquiry.
- Defence-in-depth: two independent masking layers; both must fail for PII to escape.

**Negative / Trade-offs:**

- `PiiSanitizer` adds ~50ms latency to LLM calls and ~2ms to log emission — acceptable
  but must be monitored (add `pii_sanitizer_duration_ms` to Prometheus metrics).
- Regex-based masking has false negatives for novel PII patterns — supplemented by
  Microsoft Presidio NLP-based detection for high-sensitivity contexts (LLM prompts).
- `user_id` pseudonymisation requires that the user service never logs the real-ID →
  `user_id` mapping in a system accessible to the observability backend.

## Review Criteria

Revisit this decision if:

- ANPD (Brazilian DPA) issues guidance that requires stronger anonymisation
  (irreversible) rather than pseudonymisation for observability data.
- `PiiSanitizer` false negative rate (measured in security audits) exceeds 1% —
  upgrade to full NLP-based detection (Presidio) for all fields, not just LLM prompts.
- A new PII category is identified in the DPIA/RIPD (ADR-0029) — add masking rule
  and update this ADR.

## References

- LGPD (Lei 13.709/2018) Art. 46 — Security measures for personal data protection
- GDPR (EU 2016/679) Art. 5(1)(f) — Integrity and confidentiality principle
- Microsoft Presidio — github.com/microsoft/presidio (NLP-based PII detection)
- `docs/adr/ADR-0012-opentelemetry-instrumentation-standard.md` — OTel pipeline where masking is applied
- `docs/adr/ADR-0013-structured-json-logging-schema.md` — log schema with `user_id` definition
- `docs/adr/ADR-0028-llm-api-pii-sanitization.md` — LLM-specific sanitization gate (Phase 1)
- `docs/adr/ADR-0029-dpia-ripd-production-gate.md` — DPIA/RIPD requirement before production
- `specs/privacy/19-pii-inventory.md` — full PII inventory (to be authored, issue #14)
- CLAUDE.md §1.6 criterion 5 — hard gate: PII masking before third-party ingestion
- PRIVACY.md — data processing notice
