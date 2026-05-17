# ADR-0006: Conventional Commits + Semantic Versioning

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ4 (auditability, SLSA)

---

## Context

The project needs a commit message convention and versioning scheme that:

1. **Enables machine-readable changelogs** — `CHANGELOG.md` entries should be
   derivable from commit history, reducing manual effort and drift between
   code changes and release notes.
2. **Supports SemVer automation** — version bumps (patch / minor / major) should be
   deterministic from commit types, not manual decisions.
3. **Satisfies SLSA Level 2 provenance** — every artifact version must be traceable
   to a specific commit with a structured, auditable message.
4. **Aligns with the PR squash strategy (ADR-0005)** — one squash commit per PR means
   the commit message IS the PR summary; it must carry enough semantic information.
5. **Is tooling-agnostic** — the convention must work without mandatory commit tooling
   so it does not block contribution in low-friction environments.

## Decision

We adopt **Conventional Commits v1.0.0** as the commit message specification and
**Semantic Versioning 2.0.0 (SemVer)** as the version scheme.

### Commit message format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Allowed types and their SemVer mapping

| Type       | When to use                             | SemVer bump |
| ---------- | --------------------------------------- | ----------- |
| `feat`     | New feature or capability               | MINOR       |
| `fix`      | Bug fix                                 | PATCH       |
| `hotfix`   | Critical production fix                 | PATCH       |
| `refactor` | Code restructuring, no behaviour change | none        |
| `docs`     | Documentation only                      | none        |
| `chore`    | Tooling, dependencies, CI               | none        |
| `security` | Security fix or hardening               | PATCH       |
| `test`     | Adding or updating tests                | none        |
| `perf`     | Performance improvement                 | PATCH       |

**Breaking change:** append `!` after type (`feat!`) OR include `BREAKING CHANGE:` in
the footer. Either triggers a MAJOR version bump.

### Scope convention

Scope is the primary subsystem affected:

```
agents | guardrails | observability | api | infra | adr | specs | skills | harness | ci
```

### Examples

```
feat(agents): add TriageAgent severity scoring with Golden Signals
fix(guardrails): correct HITL approval token expiry validation
docs(adr): architecture & design ADRs 0001–0004
chore(ci): pin claude-sonnet-4-6 in LLM integration tests
feat!(api): remove v1 incident endpoint — consumers must migrate to v2
```

### Versioning scheme

- `0.x.y` — Pre-production research prototype (current phase)
- `1.0.0` — First production-ready release (post-dissertation, all ADRs merged,
  DPIA/RIPD approved)
- Tags are applied to `main` after release gate passes: `git tag v0.x.y`
- `CHANGELOG.md` is updated at every release tag using the commit history

### CHANGELOG entry format

Every `[Unreleased]` section entry must reference the issue, ADR or PR number:

```markdown
- `feat(agents)` — TriageAgent severity scoring with Golden Signals (issue #X, PR #Y)
```

## Alternatives Considered

| Alternative                        | Pros                                                                            | Cons                                                                                         |
| ---------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Free-form commit messages**      | Zero overhead                                                                   | No machine-readable history; CHANGELOG must be written manually; fails SLSA provenance       |
| **Angular commit convention**      | Well-known; tooling support                                                     | Superset of Conventional Commits with extra rules; no advantage for this project             |
| **Conventional Commits v1.0.0** ✅ | Widely adopted; tooling-agnostic; deterministic SemVer mapping; SLSA-compatible | Requires discipline; typos in type break automation — mitigated by PR template type selector |
| **CalVer (calendar versioning)**   | Release date embedded in version                                                | Does not express API compatibility signals; not standard for library/service versioning      |

## Consequences

**Positive:**

- CHANGELOG generation is partially automatable — `git log --oneline` filtered by
  type produces a draft that only needs linking of issue/PR numbers.
- SemVer makes API compatibility commitments explicit — important for the evaluation
  harness that depends on stable agent API contracts.
- SLSA Level 2: every artifact version traces to a structured commit message with
  type, scope and description — satisfies provenance requirements.
- PR template type checkboxes (`.github/pull_request_template.md`) guide contributors
  to pick the right type without memorising the spec.

**Negative / Trade-offs:**

- Scope typos or wrong type choices create noise in changelog automation; mitigated
  by the PR template selector and reviewer checklist item.
- No linting enforced at commit time (no `commitlint` hook required) — relying on
  PR review discipline to keep messages clean. Add `commitlint` if automation quality
  degrades.

## Review Criteria

Revisit this decision if:

- CHANGELOG automation quality is low (> 20% of entries need manual correction) —
  add `commitlint` as a pre-commit hook.
- A second contributor joins and commit message quality becomes inconsistent — enforce
  `commitlint` in the PR gate harness (ADR-0007).

## References

- Conventional Commits v1.0.0 — conventionalcommits.org
- Semantic Versioning 2.0.0 — semver.org
- Keep a Changelog v1.1.0 — keepachangelog.com
- SLSA (Supply-chain Levels for Software Artifacts) Level 2 — slsa.dev
- `docs/adr/ADR-0005-trunk-based-development-branching.md` — squash merge strategy
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — PR gate enforces PR template
- CLAUDE.md §4.2 — Conventional Commits glossary entry
