# ADR-0005: Trunk-Based Development as Branching Strategy

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ4 (auditability)

---

## Context

The project requires a branching strategy that:

1. **Maximises integration frequency** — the primary research artifact is a working system;
   long-lived divergent branches delay integration and mask defects.
2. **Keeps `main` always deployable** — every commit to `main` must pass all harness gates,
   so the dissertation evaluation environment can be reproduced at any commit.
3. **Supports a solo researcher** — a strategy designed for large distributed teams
   (e.g. Gitflow with `develop`, `release`, `hotfix` branches) adds coordination overhead
   that is pure waste in a single-contributor project.
4. **Aligns with DORA metrics** — the four DORA metrics (Deployment Frequency, Lead Time
   for Changes, Change Failure Rate, Time to Restore) all improve with smaller, more
   frequent integrations to a single trunk.
5. **Enforces linear history** — squash merges keep `git log` readable and map one PR
   to one logical change, which is required for CHANGELOG traceability (ADR-0006).

## Decision

We adopt **Trunk-Based Development (TBD)** as the branching strategy.

Rules:

| Rule                         | Detail                                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------------------------- |
| Single long-lived branch     | `main` is the only permanent branch                                                                |
| Short-lived feature branches | Named `feature/N-short-description` where N is the issue number; merged within 1–3 days of opening |
| Merge strategy               | Squash and merge — one commit per PR on `main`                                                     |
| Direct push to `main`        | Forbidden (branch protection, ADR-0007); all changes via PR                                        |
| Branch naming                | `feature/N-*`, `fix/N-*`, `hotfix/N-*`, `docs/N-*`, `chore/N-*`                                    |
| Stale branch policy          | Branches older than 7 days without activity are deleted                                            |

`main` is the integration point, the deployment source and the dissertation artifact.
Every merge to `main` must pass the full PR gate harness (ADR-0007).

## Alternatives Considered

| Alternative                                     | Pros                                                                                           | Cons                                                                                                            |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Gitflow** (main + develop + release + hotfix) | Clear release isolation; familiar to many teams                                                | Three to five long-lived branches; high overhead for solo contributor; delayed integration hides defects longer |
| **GitHub Flow** (main + feature)                | Simple; similar to TBD                                                                         | No explicit rule on branch lifetime or naming; merge strategy unspecified                                       |
| **Trunk-Based Development** ✅                  | Shortest integration cycle; DORA-aligned; enforces discipline via PR gates not branch topology | Requires strong PR gates (ADR-0007) and harness (issue #21) to prevent `main` from breaking                     |
| **Feature flags only (no branches)**            | Zero merge conflicts                                                                           | Too risky without a full feature-flag infrastructure; out of scope for research prototype                       |

## Consequences

**Positive:**

- DORA Lead Time for Changes minimised — feature branch to `main` in 1–3 days.
- `main` is always in a deployable, reproducible state — dissertation evaluation
  environment can be restored at any commit SHA.
- Linear squash history makes CHANGELOG automation and SemVer tagging reliable (ADR-0006).
- Simpler mental model for a solo researcher; no branch synchronisation overhead.

**Negative / Trade-offs:**

- Requires strong PR gate harness (ADR-0007) — without it, `main` can break. Mitigated
  by making the harness a hard prerequisite (Phase 4, issue #21).
- Short branch lifetime creates pressure to decompose work into small PRs — a discipline
  overhead that is also a quality benefit.

## Review Criteria

Revisit this decision if:

- A second contributor joins and simultaneous feature development creates merge conflicts
  frequently enough to justify a short-lived `develop` branch.
- The evaluation experiment design requires a parallel `experiment/` branch that lives
  longer than 3 days — create a time-bounded exception ADR.

## References

- Forsgren, N., Humble, J., Kim, G. (2018). _Accelerate_. IT Revolution Press. (DORA metrics)
- Hammant, P. (2020). _Trunk Based Development_. trunkbaseddevelopment.com
- `docs/adr/ADR-0006-conventional-commits-semver.md` — commit convention built on TBD squash history
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — gates that protect `main`
- CLAUDE.md §1.4 — SDLC pillar
