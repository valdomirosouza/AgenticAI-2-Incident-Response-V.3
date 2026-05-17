# Skill: Spec Template

**Domain**: engineering
**Activation triggers**: Spec, SDD, spec-driven development, new spec, system contract, spec creation, write spec, spec template
**References**: specs/README.md, CLAUDE.md §2, RULE-001

---

## When to Write a Spec

Write a spec before implementing **any** artifact: code, configuration, documentation,
diagram, or infrastructure. If no approved spec exists, create it first and await
confirmation before proceeding (RULE-001).

> The spec is the contract. Implementation that deviates from the spec must update the spec via PR — not just the code.

---

## Spec Naming Convention

```
specs/<domain>/<NN>-<title-kebab-case>.md
```

Domain directories:

| Directory              | Content                                            |
| ---------------------- | -------------------------------------------------- |
| `specs/system/`        | Architecture, agents, lifecycle (owner: Tech Lead) |
| `specs/sdlc/`          | DoD, branching, PR process, release                |
| `specs/observability/` | Golden signals, logs, traces, SLOs                 |
| `specs/security/`      | Threat model, SAST/DAST, secrets, supply chain     |
| `specs/ethics/`        | Autonomy boundaries, audit trail, bias audit       |
| `specs/privacy/`       | PII inventory, retention, DPIA/RIPD, anonymization |

`NN` is sequential within the project (00–22 are taken; start new specs from 23+).

---

## Spec Template

```markdown
# Spec NN: <Title>

**Domain**: <domain>
**Owner**: <role — Tech Lead | SRE Lead | Security Lead | DPO>
**Status**: Draft | Approved
**Date**: YYYY-MM-DD
**Issue**: #N
**Linked ADRs**: ADR-XXXX, ADR-YYYY
**Review cadence**: <when and by whom>

---

## 1. Purpose

One paragraph: what this spec defines and why it exists.
Reference the research question (RQ1–RQ4) or project objective (O1–O5) it serves.

---

## 2. Context

What problem does this spec solve?
What pressure, constraint, or compliance requirement triggered it?
What is out of scope?

---

## 3. Decision

### 3.1 <Sub-topic>

Concrete, auditable decisions. Use tables, code blocks, and diagrams liberally.
Every decision must be testable against the Acceptance Criteria in §4.

> Guidelines:
>
> - Write decisions in present tense: "The system uses X", not "The system will use X".
> - Include exact thresholds, field names, event types, and format examples.
> - Reference related specs by file path, not by title.
> - If the decision depends on an ADR, name the ADR explicitly.

---

## 4. Acceptance Criteria

A checkbox list. CI and code review verify these before merge.
Every criterion must be independently verifiable — no vague criteria.

- [ ] Criterion 1: exact, observable, pass/fail
- [ ] Criterion 2
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                   |
| -------- | ------------------------------------------- |
| ADR-XXXX | One sentence on how this spec implements it |
| ADR-YYYY |                                             |

---

## References

- Related specs: `specs/<domain>/<file>.md`
- External standards: [ABNT citation if required by RULE-002]
```

---

## Authoring Rules

### Mandatory sections

All five sections are mandatory. A spec without all five sections is incomplete and
cannot be merged.

| Section             | Purpose                            | Failure if missing                         |
| ------------------- | ---------------------------------- | ------------------------------------------ |
| Purpose             | Explains why the spec exists       | Reviewer cannot assess scope               |
| Context             | Explains the problem being solved  | Decisions appear unmotivated               |
| Decision            | States the binding contract        | Implementation has no authoritative source |
| Acceptance Criteria | Defines verifiable done conditions | PR review has no checklist                 |
| Linked ADRs         | Traces to architectural decisions  | ADR governance breaks                      |

### Quality rules

- Write decisions in **present tense** ("The system uses…"), not future tense.
- Include **exact values**: thresholds, field names, event types, format examples.
- No vague criteria: "works correctly" is not a criterion; "returns HTTP 200 with schema X" is.
- **Privacy specs** (`specs/privacy/`) require DPO + Legal review before merge.
- **Security specs** (`specs/security/`) require Security Lead + Tech Lead review before merge.
- Every spec covering PII processing must include a data flow diagram (DFD).
- Every spec covering agent autonomy must reference `specs/ethics/16-autonomy-boundaries.md`.

---

## SDD Cycle Reminder

```
SPEC (draft) → REVIEW → APPROVE (status: Approved) → IMPLEMENT → HARNESS → MERGE
```

- Spec must reach **Approved** status before the implementation PR is opened.
- If implementation reveals a gap in the spec, update the spec in the same PR.
- Spec and implementation must be in the same PR or the spec PR must be merged first.

---

## Review Cadence by Domain

| Domain           | Mandatory reviewers         | Cadence                            |
| ---------------- | --------------------------- | ---------------------------------- |
| `system/`        | Tech Lead + Engineering     | Every major release                |
| `sdlc/`          | Engineering Lead            | Quarterly or on process change     |
| `observability/` | SRE Lead                    | Quarterly or on SLO change         |
| `security/`      | Security Lead + Tech Lead   | Every release + on CVE event       |
| `ethics/`        | Tech Lead + Ethics + Legal  | Semi-annually or on model change   |
| `privacy/`       | DPO + Legal + Security Lead | Before every production PII change |
