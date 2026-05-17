# ADR-0016: STRIDE as Mandatory Threat Modeling Method

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Security Lead — researcher)
**Affected RQs**: RQ1 (architecture), RQ4 (security compliance)

---

## Context

The Agentic AI Copilot is a security-sensitive system: it has write access to production
services (RemediationAgent), processes observability data that may contain PII, and
orchestrates LLM calls with external APIs. Before implementing any component, the
threat surface must be systematically analysed.

Requirements for the threat modeling method:

1. **Systematic coverage** — must produce a repeatable, exhaustive enumeration of
   threats across all six threat categories relevant to distributed systems.
2. **Tool-agnostic** — must be executable without licensed tooling so it is
   reproducible in the open dissertation replication package.
3. **Widely recognised** — the method must be accepted by security reviewers and
   consistent with NIST SP 800-154 (Guide to Data-Centric System Threat Modeling)
   and ISO 27005 (Information security risk management).
4. **Applicable to AI/agent systems** — must be extensible to cover LLM-specific
   threat categories (prompt injection, model data poisoning) not present in
   traditional system threat models.

## Decision

We adopt **STRIDE** (Microsoft, Shostack 2014) as the mandatory threat modeling method
for all components in this project. A STRIDE analysis is required before the
implementation spec of any component that crosses a trust boundary.

### STRIDE categories applied to this system

| Threat                     | Definition                                   | Example in this system                                     |
| -------------------------- | -------------------------------------------- | ---------------------------------------------------------- |
| **S**poofing               | Impersonating another identity               | Fake incident event injected into the detection pipeline   |
| **T**ampering              | Modifying data in transit or at rest         | Runbook content altered to produce a malicious remediation |
| **R**epudiation            | Denying an action was performed              | Agent claims it never dispatched a remediation action      |
| **I**nformation Disclosure | Exposing information to unauthorised parties | PII leaking through observability pipeline to LLM API      |
| **D**enial of Service      | Making a component unavailable               | Flooding the DetectionAgent with synthetic alerts          |
| **E**levation of Privilege | Gaining higher access than authorised        | TriageAgent bypassing HITL gate to execute remediation     |

### LLM-specific threat extensions

STRIDE is extended with two LLM-specific threat categories for any component that
uses an LLM (ADR-0003):

| Extension                | OWASP LLM ref | Mitigation                                                                 |
| ------------------------ | ------------- | -------------------------------------------------------------------------- |
| **Prompt Injection**     | LLM01         | Input sanitisation before LLM dispatch; output validation after (ADR-0021) |
| **Model Data Poisoning** | LLM03         | Runbook store integrity checks; signed corpus provenance                   |

### Threat model artifacts

Each component threat model produces:

1. A data flow diagram (DFD) at Level 1 (process + data store + external entity + data flow).
2. A STRIDE threat table: one row per identified threat, with severity (CVSS v3.1),
   mitigation strategy, and residual risk acceptance.
3. A trust boundary map: explicit list of every trust boundary crossed and the
   authentication/authorisation control at each boundary.

Threat model documents are stored in `docs/threat-models/<component>.md` and reviewed
by the Security Lead before the corresponding implementation spec is approved.

## Alternatives Considered

| Alternative                               | Pros                                                                                                      | Cons                                                                                         |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **PASTA** (Process for Attack Simulation) | Business-risk aligned; attacker-centric                                                                   | Complex; requires threat intelligence input not available for a research prototype           |
| **LINDDUN**                               | Purpose-built for privacy threat modeling                                                                 | Limited to privacy threats; does not cover integrity, availability or elevation of privilege |
| **OCTAVE**                                | Organisational risk-focused                                                                               | Designed for enterprise risk programs, not component-level engineering analysis              |
| **STRIDE** ✅                             | Systematic 6-category enumeration; tool-agnostic; well-documented in NIST/ISO; extensible for LLM threats | Does not inherently prioritise threats by likelihood — mitigated by CVSS v3.1 scoring        |

## Consequences

**Positive:**

- Every component threat model covers the full STRIDE surface — no threat category
  is accidentally omitted.
- LLM extension covers prompt injection (OWASP LLM01) and data poisoning (OWASP LLM03)
  by construction — satisfies EU AI Act Art. 9 risk management requirement.
- NIST SP 800-154 and ISO 27005 alignment: threat modeling evidence available for
  security audit and dissertation appendix.
- Tool-agnostic: threat models are Markdown tables + DFDs (Mermaid) — no licensed
  tooling required.

**Negative / Trade-offs:**

- STRIDE does not natively produce a risk-ranked backlog — CVSS scoring is added
  manually per threat. Adds ~30 minutes per component threat model.
- Trust boundary identification requires architecture clarity — STRIDE depends on
  ADR-0001 (C4 Model) diagrams being current and accurate.

## Review Criteria

Revisit this decision if:

- A purpose-built AI/agent threat modeling framework matures to the point where it
  covers STRIDE + LLM extensions in a single pass.
- ISO 27005 is updated with AI-specific guidance that introduces a required
  threat modeling method incompatible with STRIDE.

## References

- Shostack, A. (2014). _Threat Modeling: Designing for Security_. Wiley.
- NIST SP 800-154 — Guide to Data-Centric System Threat Modeling
- ISO/IEC 27005:2022 — Information security risk management
- OWASP LLM Top 10 (2025) — LLM01 (Prompt Injection), LLM03 (Training Data Poisoning)
- EU AI Act (2024) Art. 9 — Risk management system
- `docs/adr/ADR-0021-owasp-llm-top10-checklist.md` — LLM-specific mitigations
- `specs/security/12-threat-model.md` — threat model spec (to be authored, issue #12)
