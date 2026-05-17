# ADR-0027: Privacy by Design as Mandatory Principle Across All SDLC Phases

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / DPO / Privacy Lead — researcher)
**Affected RQs**: RQ4 (privacy compliance)

---

## Context

Privacy by Design (PbD) is not a feature to be added after the system is built — it is
an architectural property that must be embedded from the first spec through to production
deployment. Both LGPD art. 46 and GDPR art. 25 mandate technical and organisational
measures for data protection by design and by default.

The Copilot processes observability data that may contain PII (ADR-0014), sends prompts
to external LLM APIs (ADR-0028), generates post-mortems with incident participant
information (ADR-0010), and maintains an audit trail of agent decisions (ADR-0024).
Without PbD embedded in the SDLC, privacy controls are retrofitted inconsistently.

The seven foundational principles of Privacy by Design (Cavoukian, 2009) provide the
operationalisation framework. Each principle must be enforced at a specific SDLC gate.

## Decision

**Privacy by Design is a mandatory, non-optional principle at every SDLC phase.**
The following PbD checklist gate is enforced at each phase transition:

### PbD principles and SDLC enforcement points

| PbD Principle                      | Enforcement point      | How enforced                                                                             |
| ---------------------------------- | ---------------------- | ---------------------------------------------------------------------------------------- |
| **1. Proactive, not reactive**     | Spec review gate       | Spec must include a Privacy Impact section before approval                               |
| **2. Privacy as default**          | PR gate G10 (ADR-0007) | PII static scan blocks merge on any unmasked PII field                                   |
| **3. Privacy embedded in design**  | Architecture review    | C4 diagrams (ADR-0001) must label all personal data flows                                |
| **4. Full functionality**          | Design review          | Privacy controls must not degrade system functionality — trade-offs documented in ADR    |
| **5. End-to-end security**         | Release gate           | DPIA/RIPD completed before production deploy (ADR-0029); PII masking verified (ADR-0014) |
| **6. Visibility and transparency** | PRIVACY.md, ADRs       | All processing purposes documented and public; data subject rights operational           |
| **7. Respect for user privacy**    | Data retention TTL     | Automated deletion enforced per ADR-0030; anonymization per ADR-0031                     |

### Mandatory Privacy Impact section in every spec

Every spec in `specs/` that involves personal data processing must include a
**Privacy Impact** section with the following fields:

```markdown
## Privacy Impact

| Field                          | Value                           |
| ------------------------------ | ------------------------------- |
| Personal data processed        | [list PII categories]           |
| Legal basis (LGPD)             | [art. 7 item]                   |
| Legal basis (GDPR)             | [art. 6(1) letter]              |
| Retention period               | [per ADR-0030]                  |
| Anonymization/pseudonymization | [per ADR-0031]                  |
| Cross-border transfer          | [yes/no — if yes, per ADR-0032] |
| PII masking required           | [yes/no — if yes, per ADR-0014] |
```

Specs that process no personal data must explicitly state: `Personal data processed: None`.

### Privacy review in PR checklist

The PR template reviewer checklist includes a mandatory Privacy dimension:

- No PII in logs or traces without masking?
- No PII in test fixtures or CI artifacts (RULE-C03)?
- `user_id` used as opaque identifier — never name/email?
- New data processing purpose documented in spec Privacy Impact section?

### Data minimisation default

By default, no personal data is collected, stored or processed unless explicitly required
by a documented purpose. New data fields require a spec change and Privacy Lead approval
before implementation.

## Alternatives Considered

| Alternative                                            | Pros                                                                                        | Cons                                                                                                |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Privacy as an afterthought (end-of-project review)** | Zero ongoing overhead                                                                       | LGPD art. 46 / GDPR art. 25 violated; retrofitting controls is expensive and error-prone            |
| **Privacy checklist at release only**                  | Low ongoing friction                                                                        | Privacy issues caught too late; spec-level design flaws not correctable without major rework        |
| **Privacy by Design at all SDLC phases** ✅            | LGPD/GDPR compliant; privacy defects caught earliest; data minimisation enforced by default | Adds Privacy Impact section to every spec — small but real overhead; justified by legal requirement |

## Consequences

**Positive:**

- LGPD art. 46 and GDPR art. 25 satisfied: technical measures for privacy by design
  are embedded in the SDLC process, documented in ADRs and enforced by harness gates.
- Privacy defects are caught at spec and PR review — cheapest time to fix.
- Data minimisation default prevents accidental PII collection that would require
  retroactive DPIA/RIPD amendment.

**Negative / Trade-offs:**

- Privacy Impact section adds ~30 minutes to spec authoring time.
- Specs that claim `Personal data processed: None` require validation during PR review
  to prevent false-negative declarations.

## Review Criteria

Revisit this decision if:

- ANPD or a supervisory authority issues binding guidance that requires additional
  PbD controls not covered here.
- The Privacy Impact section format is found insufficient during the first DPIA/RIPD
  review (ADR-0029) — expand the template.

## References

- Cavoukian, A. (2009). _Privacy by Design: The 7 Foundational Principles_. IPC Ontario.
- LGPD (Lei 13.709/2018) Art. 46 — Security and privacy technical measures
- GDPR (EU 2016/679) Art. 25 — Data protection by design and by default
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md` — PbD principle 2 implementation
- `docs/adr/ADR-0029-dpia-ripd-before-production.md` — PbD principle 5 gate
- `docs/adr/ADR-0030-data-retention-ttl-policy.md` — PbD principle 7 implementation
- `PRIVACY.md` — transparency notice (PbD principle 6)
- CLAUDE.md §5 RULE-C03 — no PII in repository
