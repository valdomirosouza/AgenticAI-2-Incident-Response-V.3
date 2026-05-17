# Skill: Requirements

**Domain**: sdlc
**Activation triggers**: Requirements, user story, acceptance criteria, elicitation, refinement, backlog, epic, RQ, research question, functional requirement, non-functional requirement
**References**: specs/system/00-project-brief.md, CLAUDE.md §2, RULE-001

---

## Principles

- No implementation without an approved spec (RULE-001). A requirement that lacks a spec is not actionable.
- Requirements trace upward to research questions (RQ1–RQ4) or project objectives (O1–O5).
- Non-functional requirements are constraints — they must be measurable and testable.
- Language: English only (RULE-005).

---

## Requirement Types

| Type                     | Definition                                                     | Example                                                                    |
| ------------------------ | -------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **Functional**           | What the system does                                           | "DetectionAgent emits `incident.created` within 5 min of threshold breach" |
| **Non-functional (NFR)** | How well the system does it (performance, security, usability) | "MTTD P1 < 5 minutes" (measurable SLO target)                              |
| **Constraint**           | Fixed boundary — not negotiable without an ADR                 | "All PRODUCTION\_\* actions require HITL (ADR-0023)"                       |
| **Research question**    | Empirical claim to be validated through the evaluation corpus  | RQ1: "Does the Copilot reduce MTTD by ≥ 20%?"                              |

---

## Traceability Matrix

Every requirement maps to at least one spec and one acceptance criterion.

| Requirement ID | Description                         | Spec                                     | Acceptance criterion                             | RQ / Objective |
| -------------- | ----------------------------------- | ---------------------------------------- | ------------------------------------------------ | -------------- |
| REQ-F-01       | DetectionAgent detects P1 in < 5min | `specs/system/03-incident-lifecycle.md`  | MTTD P1 < 5 min in e2e test                      | O1, RQ1        |
| REQ-F-02       | RemediationAgent uses HITL gate     | `specs/ethics/16-autonomy-boundaries.md` | No PRODUCTION\_\* executes without ApprovalToken | O3             |
| REQ-S-01       | PII masked before LLM API call      | `specs/privacy/19-pii-inventory.md`      | Semgrep `llm-unsanitized-prompt` clean           | O5             |
| REQ-P-01       | Audit trail append-only             | `specs/ethics/17-audit-trail.md`         | No DELETE role exists in Vault                   | O3, O5         |

---

## User Story Format

```
As a <role>,
I want <capability>,
So that <outcome>.

Acceptance criteria:
- Given <precondition>, when <action>, then <observable result>.
- Given ..., when ..., then ...

Definition of Done: see specs/sdlc/04-definition-of-done.md
```

### Roles for this project

| Role               | Concerns                                                           |
| ------------------ | ------------------------------------------------------------------ |
| `on_call_engineer` | Receiving alerts, approving remediation, overriding HOTL decisions |
| `engineering_lead` | Reviewing post-mortems, setting severity, escalation approval      |
| `sre_lead`         | SLO thresholds, runbook quality, MTTD/MTTR targets                 |
| `dpo`              | PII handling, LGPD compliance, DPIA sign-off                       |
| `researcher`       | Accessing anonymised corpus, computing MTTD/MTTR                   |

---

## Elicitation Checklist

When eliciting or refining a requirement:

- [ ] Requirement is stated from the user's perspective (not implementation detail)
- [ ] Acceptance criterion is observable and testable (not "works correctly")
- [ ] NFRs include exact thresholds (time, rate, percentage)
- [ ] Requirement traces to RQ or objective in `specs/system/00-project-brief.md`
- [ ] Constraint requirements reference the ADR that imposes them
- [ ] Spec exists (or has been created) before the story is moved to "Ready"
- [ ] Privacy implications assessed — PII categories from `specs/privacy/19-pii-inventory.md`
- [ ] Autonomy level confirmed (HITL / HOTL / BLOCKED) per `specs/ethics/16-autonomy-boundaries.md`

---

## Out-of-Scope Boundary

| In scope                                                | Out of scope                                |
| ------------------------------------------------------- | ------------------------------------------- |
| Availability, latency, error rate, saturation incidents | Security incidents (SIEM/SOC domain)        |
| Cloud-native microservice environments                  | Hardware failures                           |
| HOTL detection, triage, RCA; HITL remediation           | Fully autonomous remediation without HITL   |
| LGPD + GDPR compliance for Brazilian services           | Other jurisdictions (unless via GDPR scope) |
