# ADR-0008: Test Coverage Thresholds

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ3 (guardrail correctness)

---

## Context

Test coverage thresholds must balance three competing pressures:

1. **Correctness of safety-critical code** — guardrails, HITL gates and PII sanitizers
   are safety-critical; a bug in any of these has compliance and production impact.
   They require higher coverage than utility code.
2. **Practicality for a research prototype** — 100% coverage on all code is
   unrealistic and often misleading (covered ≠ correct). Thresholds must be
   achievable without fabricating tests to hit numbers.
3. **ISO 25010 quality model** — the standard defines Reliability and Security as
   quality characteristics measurable through test completeness and defect density.

The Hexagonal Architecture (ADR-0002) gives a natural boundary: `domain/` code is
pure logic with no I/O side effects and is cheapest to unit-test; `adapters/` code
integrates with external systems and requires integration tests with real or
containerised dependencies (RULE-C02: no synthetic fixtures).

## Decision

### Coverage thresholds by layer and criticality

| Layer / Component          | Test type          | Minimum threshold                  | Rationale                                                          |
| -------------------------- | ------------------ | ---------------------------------- | ------------------------------------------------------------------ |
| `domain/` (all agents)     | Unit               | **90%**                            | Pure logic, no I/O — cheapest to test; highest impact if wrong     |
| `ports/` (interfaces)      | Unit               | **80%**                            | Interface contracts must be verified                               |
| `adapters/` (non-critical) | Integration        | **60%**                            | External I/O; real dependencies via testcontainers                 |
| `src/guardrails/`          | Unit + Integration | **95%**                            | Safety-critical; HITL gate correctness is a compliance requirement |
| `src/api/`                 | Integration        | **80%**                            | Public contract; must cover all endpoint behaviours                |
| Overall project            | Combined           | **80%** unit / **60%** integration | PR gate G05/G06 threshold (ADR-0007)                               |

### Coverage measurement

- Tool: `pytest-cov` with `--cov-report=xml` for CI integration.
- Branch coverage (`--cov-branch`) is mandatory for `src/guardrails/` — line coverage
  alone is insufficient for conditional safety logic.
- Coverage is measured on **changed files** in PR gate (fast feedback) and on the
  **full codebase** in the release gate (ADR-0007, harness/release-check.yml).

### What coverage does NOT measure

Coverage thresholds are a floor, not a quality target. Tests must:

- Cover behaviour (input → output), not implementation details.
- Include failure and exception paths, not just happy paths.
- Use real corpus data for fixtures (RULE-C02), not synthetic mocks.

Reviewers must verify test quality, not just coverage numbers (PR template reviewer
checklist, `tests/` dimension).

## Alternatives Considered

| Alternative                             | Pros                                                    | Cons                                                                                |
| --------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **100% coverage everywhere**            | Maximum confidence                                      | Unachievable in practice; encourages coverage-gaming with trivial tests             |
| **No coverage threshold**               | Zero overhead                                           | Safety-critical guardrail code can ship undertested; ISO 25010 Reliability violated |
| **Single flat threshold (80%)**         | Simple                                                  | Does not reflect criticality difference between guardrails and adapters             |
| **Tiered thresholds by criticality** ✅ | Proportional effort; guardrails at 95%; adapters at 60% | More configuration to maintain; justified by safety-critical distinction            |

## Consequences

**Positive:**

- Guardrails and HITL gate tested at 95% branch coverage — highest confidence in the
  safety-critical path.
- Tiered thresholds avoid over-investment in adapter tests (which are inherently
  slower and more fragile) while protecting domain logic.
- ISO 25010 Reliability dimension documented with measurable thresholds.
- Coverage report in CI produces a numerical audit trail for the dissertation
  evaluation chapter.

**Negative / Trade-offs:**

- `src/guardrails/` at 95% branch coverage is ambitious — requires disciplined test
  writing from the start. Enforced from Phase 5 (issue #23) when source code begins.
- Integration tests with `testcontainers` add CI setup complexity (Docker-in-Docker
  or Colima) — must be configured in `.github/workflows/ci.yml`.

## Review Criteria

Revisit this decision if:

- Guardrail tests consistently fail to reach 95% due to untestable external
  dependencies — extract those paths to adapters, keeping domain logic at threshold.
- Overall CI time exceeds 15 minutes — consider splitting coverage gates into
  fast (unit only) and slow (integration, async) tiers.

## References

- ISO/IEC 25010:2023 — Systems and software quality model (Reliability, Security)
- `docs/adr/ADR-0002-hexagonal-architecture-agent-services.md` — layer boundaries
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — gates G05 and G06
- CLAUDE.md §5 RULE-C02 — real corpus fixtures, no synthetic mocks
- `specs/sdlc/07-test-strategy.md` — full test strategy spec (to be authored, issue #10)
