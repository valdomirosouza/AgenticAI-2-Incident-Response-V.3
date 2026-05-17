# ADR-0021: OWASP LLM Top 10 Checklist for All Agentic AI Components

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Security Lead — researcher)
**Affected RQs**: RQ3 (guardrails), RQ4 (security compliance)

---

## Context

The OWASP LLM Top 10 (2025 edition) defines the ten most critical security risks for
applications built on Large Language Models. The Copilot is an Agentic AI system that
uses an LLM for reasoning (ADR-0003), routes LLM outputs to production actions
(RemediationAgent), and ingests external data (runbooks, observability signals, post-mortems)
as LLM context. This makes it one of the highest-risk LLM application categories.

EU AI Act Art. 9 requires that high-risk AI systems implement a risk management system
covering all foreseeable risks. The OWASP LLM Top 10 is the industry-standard risk
taxonomy for LLM systems and is referenced in CLAUDE.md §1.5 as a mandatory compliance
baseline.

## Decision

The **OWASP LLM Top 10 (2025)** checklist is mandatory for every component that
uses an LLM or processes LLM outputs. The checklist is applied at three points:

1. **Design review** — before the component spec is approved.
2. **PR review** — reviewer checklist item for all PRs touching `src/agents/`, `src/guardrails/`, `src/adapters/outbound/llm_adapter.py`.
3. **Release gate** — a structured checklist artifact is generated and attached to every release.

### Full checklist with chosen mitigations

| #         | Risk                             | Severity | Mitigation in this system                                                                                                                            |
| --------- | -------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **LLM01** | Prompt Injection                 | Critical | Input sanitisation before LLM dispatch (`PiiSanitizer`); structured output enforcement (JSON mode); Semgrep custom rule detects unsanitised concat   |
| **LLM02** | Sensitive Information Disclosure | High     | PII masking gate (ADR-0014) before prompt dispatch; output validation strips PII before logging                                                      |
| **LLM03** | Supply Chain                     | High     | LLM model pinned by exact ID (`claude-sonnet-4-6`); SBOM includes `anthropic` SDK version (ADR-0019); dependency hash verification (ADR-0022)        |
| **LLM04** | Data and Model Poisoning         | High     | Runbook store uses signed corpus provenance; STRIDE threat model (ADR-0016) covers tampered runbook vector                                           |
| **LLM05** | Improper Output Handling         | Critical | All LLM outputs parsed against typed Pydantic schema before use; schema validation failure → escalate to human, do not execute                       |
| **LLM06** | Excessive Agency                 | Critical | RemediationAgent is HITL — zero autonomous execution (ADR-0004); all tool calls validated against allow-list in `src/guardrails/action_validator.py` |
| **LLM07** | System Prompt Leakage            | Medium   | System prompts stored in Vault (ADR-0020), not in code; logs redact system prompt content                                                            |
| **LLM08** | Vector and Embedding Weaknesses  | Medium   | Runbook vector store access is read-only for agents; write access restricted to admin role with audit log                                            |
| **LLM09** | Misinformation / Overreliance    | High     | Confidence threshold gate in RCAAgent (≥ 0.6 to proceed, ADR-0004); all LLM outputs labelled as `AI-GENERATED` in HITL approval UI                   |
| **LLM10** | Unbounded Consumption            | Medium   | Per-call token budget enforced in `LLMPort` adapter; total per-incident token budget tracked; alert fires if budget exceeded by > 2×                 |

### Checklist artifact

A structured YAML checklist (`docs/security/llm-top10-checklist-<version>.yml`) is
generated at each release with the status (`mitigated`, `accepted-risk`, `open`) and
evidence reference for each item. Open items block the release gate.

### PR review integration

The PR template reviewer checklist includes:

> "OWASP LLM checklist applied (if Agentic AI code)?" — mandatory for any PR
> touching `src/agents/`, `src/guardrails/`, `src/adapters/outbound/llm_adapter.py`.

### Critical items — zero tolerance

LLM01 (Prompt Injection), LLM05 (Improper Output Handling) and LLM06 (Excessive
Agency) are classified Critical. A finding in any of these items blocks the PR gate
via the custom Semgrep rule set (ADR-0017).

## Alternatives Considered

| Alternative                   | Pros                                                                                          | Cons                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **No LLM-specific checklist** | Zero overhead                                                                                 | LLM01–LLM06 risks unmitigated; EU AI Act Art. 9 not satisfied                          |
| **Custom internal checklist** | Tailored to this system                                                                       | Not standardised; not accepted by security reviewers as evidence                       |
| **OWASP LLM Top 10** ✅       | Industry standard; EU AI Act Art. 9 evidence; PR checklist integration; release gate artifact | Requires discipline to apply at design + PR + release — mitigated by checklist tooling |

## Consequences

**Positive:**

- EU AI Act Art. 9 risk management requirement satisfied: OWASP LLM Top 10 is the
  documented risk framework with mitigations for each item.
- LLM01 (Prompt Injection) and LLM06 (Excessive Agency) mitigated at code level
  (input sanitisation, HITL gate) — the highest-impact risks for an agentic system.
- Release checklist artifact provides audit evidence for security reviews and the
  dissertation security evaluation chapter.

**Negative / Trade-offs:**

- Checklist discipline requires that every PR reviewer is familiar with the LLM Top 10
  — mitigated by linking this ADR from the PR template.
- OWASP LLM Top 10 is updated annually; the 2025 edition may add items — checklist
  must be reviewed at each edition release.

## Review Criteria

Revisit this decision if:

- OWASP publishes a 2026 edition of the LLM Top 10 with new items — update checklist
  and this ADR within 30 days of publication.
- A critical LLM vulnerability is discovered that is not covered by the current Top 10
  — add it as an LLM11+ item in the project checklist pending the next OWASP update.

## References

- OWASP LLM Top 10 (2025) — owasp.org/www-project-top-10-for-large-language-model-applications
- EU AI Act (2024) Art. 9 — Risk management system
- `docs/adr/ADR-0003-llm-provider-model-selection.md` — LLM provider and model
- `docs/adr/ADR-0004-multi-agent-orchestration-pattern.md` — HITL gate (LLM06 mitigation)
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md` — LLM02 mitigation
- `docs/adr/ADR-0016-stride-threat-modeling-method.md` — LLM04 mitigation (STRIDE)
- `docs/adr/ADR-0017-sast-mandatory-pr-gate.md` — custom Semgrep rules for LLM01/LLM05
- CLAUDE.md §1.5 — Compliance baseline (OWASP LLM Top 10)
