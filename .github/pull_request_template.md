## Description

> What does this PR do and **why**? (not how — code explains the how)

## Type

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `hotfix` — critical production fix
- [ ] `refactor` — code restructuring, no behavior change
- [ ] `security` — security fix or hardening
- [ ] `docs` — documentation only
- [ ] `chore` — tooling, dependencies, CI

## Linked Issue

Closes #

## Related ADR

> Link any ADR whose decision this PR implements or that governs this change.
> If a new architectural decision was made, create the ADR first and reference it here.

ADR: <!-- e.g. docs/adr/ADR-0007-pr-merge-gates-ci-checks.md -->

## Linked Spec

> Every PR must trace to at least one spec in `specs/` (CLAUDE.md §3.1 doc-gate).

Spec: <!-- e.g. specs/sdlc/06-pr-and-review-process.md -->

---

## Author Checklist

> Complete before requesting review. All items must be checked.

- [ ] Tests written and passing locally
- [ ] Harness run without failures (`harness/code-check.yml`)
- [ ] SAST executed — zero Critical or High findings
- [ ] Secrets and PII verified — no exposure
- [ ] Documentation updated if behavior changed
- [ ] `CHANGELOG.md` updated with an entry for this PR
- [ ] Self-review completed (full diff reviewed)

---

## Reviewer Checklist

> Guidance for reviewers. All dimensions must be assessed.

**Correctness & Logic**

- [ ] Logic correct for all cases, including edge cases?
- [ ] No race conditions or hidden side effects?

**Security**

- [ ] No input without validation/sanitization?
- [ ] No hardcoded secrets, tokens or passwords?
- [ ] PII handled per `privacy/pii.md`?
- [ ] No SQL injection, XSS, SSRF or path traversal?
- [ ] OWASP LLM checklist applied (if Agentic AI code)?

**Quality & Maintainability**

- [ ] Functions have single responsibility (SRP)?
- [ ] No dead code, loose TODOs or debug prints?
- [ ] Cyclomatic complexity ≤ 10?

**Tests**

- [ ] Tests cover behavior, not implementation?
- [ ] Failure and exception cases tested?
- [ ] Fixtures use real corpus data, not synthetic mocks (RULE-C02)?

**Observability**

- [ ] Structured logs at critical points?
- [ ] Metrics instrumented (Golden Signals)?
- [ ] `trace_id` propagated correctly?
- [ ] No PII exposed in logs or traces?

**Documentation**

- [ ] README or tech-doc updated if needed?
- [ ] ADR created if an architectural decision was made?

---

_Governed by `skills/project-skills-catalog.md → sdlc/pull-request.md` | CLAUDE.md §4.1_
