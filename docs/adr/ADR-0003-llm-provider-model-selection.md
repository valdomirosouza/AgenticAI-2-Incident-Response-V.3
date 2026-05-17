# ADR-0003: Selection of LLM Provider and Model Version

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (system architecture), RQ2 (detection/triage quality), RQ4 (compliance)

---

## Context

The Copilot's reasoning capability — incident triage, RCA hypothesis generation,
runbook selection and post-mortem synthesis — depends on a Large Language Model (LLM).
The choice of provider and model version is a foundational decision because:

1. **Quality of reasoning directly affects MTTD/MTTR outcomes** — the primary research
   metric. A weaker model degrades triage precision and recall; a stronger model may
   add latency that negates MTTD gains.
2. **Compliance requirements constrain the shortlist** — EU AI Act Art. 13 (transparency)
   requires that the AI system's capabilities and limitations be documented. OWASP LLM09
   (Overreliance) requires that model boundaries be disclosed. GDPR/LGPD require that
   PII never be sent to a third-party API without sanitization (ADR-0028).
3. **Provider stability matters for a dissertation prototype** — the model version must
   be pinnable to ensure reproducible experimental results across the evaluation period.
4. **Cost must be bounded** — this is a funded academic project; inference costs must
   remain within a predictable budget for the evaluation experiments.
5. **API quality** — the provider must support structured output (JSON mode), tool/function
   calling (for agent action dispatch), and context windows large enough to hold
   observability data (logs + traces + runbook) in a single prompt.

## Decision

We adopt **Anthropic Claude** as the primary LLM provider, with **Claude Sonnet 4.6**
(`claude-sonnet-4-6`) as the pinned model for all agent reasoning tasks in this project.

Rationale for provider:

- Claude's Constitutional AI training provides stronger safety properties for autonomous
  agent use cases — reduced likelihood of hallucinated remediation actions.
- Native tool/function calling via the Anthropic API supports agent action dispatch
  without prompt engineering workarounds.
- 200K token context window accommodates full observability context (logs, metrics,
  traces, runbook) in a single call — critical for RCA quality.
- Model versions are pinnable by exact ID (`claude-sonnet-4-6`) ensuring reproducible
  experimental results.
- API terms explicitly support research use; GDPR/LGPD-compliant data processing
  agreement available.

Rationale for model tier (Sonnet vs. Opus vs. Haiku):

| Criterion            | Haiku         | Sonnet ✅ | Opus      |
| -------------------- | ------------- | --------- | --------- |
| Reasoning quality    | Adequate      | Strong    | Strongest |
| Latency (p50)        | ~1s           | ~3–5s     | ~10–15s   |
| Cost per 1M tokens   | Low           | Medium    | High      |
| Suitability for MTTD | Risk of drift | Balanced  | Too slow  |

Sonnet is the balanced choice: reasoning quality sufficient for triage/RCA, latency
compatible with MTTD targets, cost bounded for academic evaluation.

**Pinned model ID:** `claude-sonnet-4-6`
**Fallback model:** `claude-haiku-4-5-20251001` (for high-frequency, low-complexity tasks
such as alert classification and log summarization where cost and latency dominate)

**PII sanitization gate:** All prompts MUST pass through the PII sanitizer
(to be implemented in `src/guardrails/pii_sanitizer.py`) before dispatch to the API.
This is a hard gate enforced at the `LLMPort` outbound adapter — not optional
(ADR-0028, RULE-C03, GDPR Art. 6, LGPD Art. 7).

## Alternatives Considered

| Alternative                     | Pros                                                                                             | Cons                                                                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| **OpenAI GPT-4o**               | Widely benchmarked; strong tool use                                                              | Less safety-oriented for autonomous agents; higher prompt injection surface (OWASP LLM01); data residency concerns for LGPD |
| **Google Gemini 1.5 Pro**       | 1M token context; strong multimodal                                                              | API maturity lower for structured agent use; limited LGPD-compliant DPA documentation                                       |
| **Mistral Large / self-hosted** | Full data sovereignty; no third-party PII risk                                                   | Self-hosting GPU infra out of scope for dissertation; model quality lower for RCA reasoning                                 |
| **Llama 3 (self-hosted)**       | Open weights; zero API cost; full reproducibility                                                | Same infra constraint as Mistral; context window limits observability data ingestion                                        |
| **Anthropic Claude Sonnet** ✅  | Constitutional AI safety; pinnable versions; 200K context; structured output; LGPD-compliant DPA | Third-party API — requires PII gate (mitigated by ADR-0028)                                                                 |

## Consequences

**Positive:**

- Pinnable model ID ensures reproducible experimental results — essential for
  dissertation validity (RULE-003: distinguish real evidence from toy examples).
- Constitutional AI training reduces hallucinated remediation actions — directly
  supports safe HITL/HOTL autonomy model (CLAUDE.md §1.3).
- 200K context window enables full-context RCA without chunking, improving hypothesis
  quality and reducing multi-call latency.
- EU AI Act Art. 13 compliance: model identity, version and limitations are documented
  here and referenced in the system transparency report.

**Negative / Trade-offs:**

- Third-party API dependency: if Anthropic deprecates `claude-sonnet-4-6`, the
  pinned model ID becomes unavailable — mitigated by the fallback model and the Port
  interface (ADR-0002) allowing adapter swap without domain changes.
- API cost is variable; budget overrun risk in large-scale evaluation — mitigated by
  per-experiment token budgeting in the evaluation harness.
- PII sanitization gate adds latency (~50–100ms) per LLM call — acceptable given
  MTTD target of minutes, not seconds.
- OWASP LLM09 (Overreliance): system must not execute remediation actions based solely
  on LLM output — enforced by HITL gate (CLAUDE.md §1.3, ADR-0004).

## Review Criteria

Revisit this decision if:

- `claude-sonnet-4-6` is deprecated by Anthropic and a direct replacement is not
  available with equivalent capabilities.
- Evaluation experiments show that reasoning quality is insufficient for MTTD/MTTR
  targets — consider upgrading to Opus tier.
- A self-hosted open-weight model reaches sufficient quality and the research scope
  expands to include data sovereignty as a variable.
- ANPD or a supervisory authority issues guidance that changes the cross-border
  transfer assessment for Anthropic's infrastructure (ADR-0032).

## References

- Anthropic. (2024). _Claude Model Documentation_. anthropic.com
- OWASP LLM Top 10 (2025) — LLM01 (Prompt Injection), LLM09 (Overreliance)
- EU AI Act (2024) Art. 13 — Transparency and provision of information to users
- GDPR Art. 6 — Lawfulness of processing; Art. 46 — Transfers by appropriate safeguards
- LGPD Art. 7 — Legal bases for processing; Art. 33 — International data transfer
- `docs/adr/ADR-0028-llm-api-pii-sanitization.md` — PII sanitization gate (Phase 1)
- `docs/adr/ADR-0032-cross-border-data-transfer-safeguards.md` — Transfer safeguards (Phase 1)
- `docs/adr/ADR-0002-hexagonal-architecture-agent-services.md` — LLMPort interface
- CLAUDE.md §1.5 — Compliance baseline
