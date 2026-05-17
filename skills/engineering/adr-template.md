# Skill: ADR Template

**Domain**: engineering
**Activation triggers**: ADR, architecture decision, architectural decision record, decision to document, significant decision, new tool selection, framework choice, policy change
**References**: docs/adr/README.md, CLAUDE.md §6, ADR-0001 to ADR-0032

---

## When to Create an ADR

Create an ADR when you (CLAUDE.md §6.1):

- Alter SLR inclusion/exclusion criteria or the search string
- Add or remove a research database
- Alter quality rubrics (QA1–QA4)
- Make a system architectural decision (agent framework, LLM model, library)
- Change the dissertation chapter structure
- Override or supersede an existing ADR
- Adopt a new tool that affects the CI pipeline, observability stack, or data processing

> **Do not** create an ADR for: bug fixes, documentation updates, minor config changes, test additions.

---

## Naming Convention

```
docs/adr/ADR-NNNN-title-kebab-case.md
```

`NNNN` is a zero-padded sequential integer. The next available number is always one
higher than the highest existing ADR in `docs/adr/`. Check before numbering.

Examples:

```
docs/adr/ADR-0033-vector-database-selection.md
docs/adr/ADR-0034-kafka-topic-schema-registry.md
```

---

## ADR Template

```markdown
# ADR-NNNN: [Decision Title]

**Status**: Proposed
**Date**: YYYY-MM-DD
**Deciders**: [names or roles — no real names if privacy-sensitive]
**Affected RQs**: [RQ1 | RQ2 | RQ3 | RQ4 | N/A]

---

## Context

[Describe the situation that made this decision necessary.
What problem was being solved? What pressure or constraint existed?
Reference the spec or issue that triggered the need.]

## Decision

[State the decision in affirmative, concrete terms.
"We adopt X because Y." — not "We might use X".]

## Alternatives Considered

| Alternative | Pros | Cons |
| ----------- | ---- | ---- |
| Option A    |      |      |
| Option B    |      |      |
| Option C    |      |      |

## Consequences

**Positive:**

- [Benefit 1]
- [Benefit 2]

**Negative / Trade-offs:**

- [Trade-off 1]
- [Trade-off 2]

## Review Criteria

[When should this decision be revisited? What evidence would change it?
Example: "Revisit if LLM API cost exceeds 20% of infrastructure budget for two
consecutive months."]

## References

- Spec: `specs/<domain>/<NN>-<name>.md`
- ADRs superseded: ADR-XXXX (if applicable)
- External: [link or ABNT citation]
```

---

## Status Lifecycle

```
Proposed → Accepted → [Superseded by ADR-XXXX | Deprecated]
```

| Status                     | Meaning                                                                     |
| -------------------------- | --------------------------------------------------------------------------- |
| **Proposed**               | Draft — under review; implementation must not start yet                     |
| **Accepted**               | Reviewed and approved; governs the artifact it covers                       |
| **Superseded by ADR-XXXX** | Replaced — the new ADR takes effect; this one is read-only history          |
| **Deprecated**             | No longer applicable; no replacement needed (e.g. feature removed entirely) |

> Overriding an Accepted ADR requires a new ADR with status Proposed → Accepted first.
> Never edit the body of an Accepted ADR — create a superseding one.

---

## Authoring Rules

1. **One decision per ADR.** If two decisions are coupled, write two ADRs and link them.
2. **Context before alternatives.** The reader must understand the problem before the solution.
3. **Concrete alternatives.** Name the tools or patterns actually considered — not "Option A / Option B".
4. **Affected RQs.** Every ADR that touches agent behaviour, metrics, or the evaluation corpus must list the affected research question.
5. **English only** (RULE-005).
6. **No ADR about itself.** You cannot write an ADR that only says "we decided to write ADRs".

---

## Integration with the SDD Cycle

- ADR must be merged with status **Accepted** before the spec that implements it can be opened.
- Spec must be merged before the implementation PR that depends on it.
- ADR numbers must appear in spec `## Linked ADRs` table and in implementation PR description.

---

## Quick Reference: Foundational ADR Index

All 32 foundational ADRs are listed in `docs/adr/README.md` with their governed skills
and compliance drivers. Before writing a new ADR, confirm that the decision is not
already covered by ADR-0001–ADR-0032.

| Domain                 | ADR range     |
| ---------------------- | ------------- |
| Architecture & Design  | ADR-0001–0004 |
| SDLC & Engineering     | ADR-0005–0010 |
| Observability          | ADR-0011–0015 |
| DevSecOps & Security   | ADR-0016–0022 |
| Ethics & AI Governance | ADR-0023–0026 |
| Privacy & Data         | ADR-0027–0032 |
