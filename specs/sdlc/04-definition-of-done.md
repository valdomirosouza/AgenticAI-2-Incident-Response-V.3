# Spec 04: Definition of Done

**Domain**: sdlc
**Owner**: Engineering Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #10
**Linked ADRs**: ADR-0007, ADR-0008
**Review cadence**: Quarterly or on process change; all engineers must review DoD changes

---

## 1. Purpose

Define what "done" means for every story type in this project. A story is not done until
every checkbox in its type-specific DoD is checked. This spec is the authoritative
reference — not individual interpretation or verbal agreement.

---

## 2. Context

Without a formal DoD, "done" drifts. Stories are merged without tests, without
observability, without security review — and the gaps compound. This project has
additional DoD requirements beyond typical software: privacy controls, LLM-specific
security checks and EU AI Act transparency obligations must be verified at story
level, not retrofitted at release.

ADR-0007 defines the 14 binary PR gates (G01–G14) that the CI pipeline enforces.
This spec defines the human-layer checklist that complements those automated gates.

---

## 3. Decision

### 3.1 Universal DoD (applies to every story type)

These items are non-negotiable regardless of story type:

- [ ] Code compiles and all existing tests pass (`pytest` green)
- [ ] No secrets, credentials or PII committed to the repository (RULE-C03)
- [ ] All new code has a corresponding unit test (minimum one happy-path + one failure case)
- [ ] PR description links the issue, spec and relevant ADR(s)
- [ ] All CI gates (G01–G14) pass green on the PR (ADR-0007, RULE-C04)
- [ ] CHANGELOG.md entry drafted (if the change warrants a user-visible entry)
- [ ] Language: English only (RULE-005)

### 3.2 DoD by story type

#### `feat` — New feature

- [ ] Universal DoD ✓
- [ ] Spec exists and is in `Approved` status before any code is written (RULE-001)
- [ ] Branch coverage ≥ 80% overall; ≥ 90% for domain layer; ≥ 95% for guardrails (ADR-0008)
- [ ] Structured logs emitted for all key code paths (ADR-0013 schema, mandatory fields)
- [ ] Distributed trace spans created for any new service boundary or external call (ADR-0012)
- [ ] Golden Signal metrics exposed for any new service endpoint (ADR-0011)
- [ ] OWASP LLM Top 10 checklist applied if the feature touches any LLM integration (ADR-0021)
- [ ] Privacy Impact assessed: new PII categories documented in `specs/privacy/19-pii-inventory.md`
- [ ] If the feature dispatches to an LLM: `sanitized=True` gate verified; Semgrep rule passes (ADR-0028)
- [ ] If the feature adds a new agent action: HITL/HOTL classification documented in `specs/system/02-agent-design.md` (ADR-0023)
- [ ] If the feature adds a new external dependency: dependency pinned with hash; CVE scan passes (ADR-0022)

#### `fix` — Bug fix

- [ ] Universal DoD ✓
- [ ] Regression test added that reproduces the bug before the fix
- [ ] Root cause documented in PR description (not just "fixed the bug")
- [ ] If the bug was a security issue: severity label `security` added; SECURITY.md updated if public disclosure warranted

#### `security` — Security improvement or vulnerability remediation

- [ ] Universal DoD ✓
- [ ] Threat model entry updated in `specs/security/12-threat-model.md` (ADR-0016)
- [ ] SAST scan (Semgrep + Bandit + CodeQL) passes with zero new Critical/High findings (ADR-0017)
- [ ] If the fix involves secrets rotation: Vault lease revoked and new credential issued (ADR-0020, ADR-0025)
- [ ] OWASP LLM checklist re-run if the fix touches LLM prompt handling (ADR-0021)
- [ ] SBOM regenerated and Grype CVE scan passes (ADR-0019)
- [ ] Security reviewer approval (in addition to standard reviewer) required

#### `docs` — Documentation update

- [ ] Universal DoD ✓
- [ ] Documentation gate (D01–D04) passes green (ADR-0007)
- [ ] If a spec changes: linked ADRs updated or new ADR created if the change is architectural
- [ ] If an ADR changes: status field updated; date field updated; Deciders field accurate
- [ ] Diagrams (C4, data flow) updated to match code if the structure changed (ADR-0001)

#### `refactor` — Code restructuring without behaviour change

- [ ] Universal DoD ✓
- [ ] All existing tests pass without modification (behaviour unchanged)
- [ ] Import linter passes: hexagonal layer boundaries respected after refactor (ADR-0002)
- [ ] No coverage regression: overall branch coverage does not decrease (ADR-0008)
- [ ] No new external dependencies introduced

#### `chore` — Tooling, CI, dependency updates

- [ ] Universal DoD ✓
- [ ] If dependency updated: hash-pinned in `requirements.lock`; Grype CVE scan passes (ADR-0022)
- [ ] If CI workflow changed: all gates still enforce zero-tolerance thresholds (ADR-0007)
- [ ] If IaC changed: Checkov scan passes (ADR-0007 G13)

### 3.3 Release DoD (additional gate before production)

Applied at the release gate in addition to all story-level DoDs:

- [ ] All 14 PR gates (G01–G14) have been green on every merged PR since last release
- [ ] DPIA/RIPD completed and signed by DPO (ADR-0029) — hard gate
- [ ] OWASP LLM Top 10 release checklist artifact generated and stored (ADR-0021)
- [ ] Bias audit completed within last 90 days for TriageAgent and RCAAgent (ADR-0026)
- [ ] SBOM published and no unmitigated Critical CVEs (ADR-0019)
- [ ] Blue-green deployment smoke tests pass in staging (ADR-0009)
- [ ] Kill-switch drill completed within last 90 days (ADR-0025)
- [ ] `PRIVACY.md` and `SECURITY.md` reviewed and up to date

---

## 4. Acceptance Criteria

- [ ] Separate DoD checklist exists for each of the 5 story types: feat, fix, security, docs, refactor, chore
- [ ] Universal DoD is defined and referenced by every type-specific checklist
- [ ] Release DoD captures all hard gates from ADR-0029, ADR-0021, ADR-0026, ADR-0025
- [ ] Each DoD item references the ADR or RULE that mandates it
- [ ] Engineering Lead review + all engineers acknowledgement recorded before first sprint
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                           |
| -------- | ------------------------------------------------------------------- |
| ADR-0002 | Hexagonal architecture — import linter check in refactor DoD        |
| ADR-0007 | PR merge gates G01–G14 — automated layer of every story DoD         |
| ADR-0008 | Test coverage thresholds — 95% guardrails, 90% domain, 80% overall  |
| ADR-0011 | Golden Signals — metrics DoD for `feat` stories                     |
| ADR-0012 | OpenTelemetry — trace spans DoD for `feat` stories                  |
| ADR-0013 | Structured JSON logging — log schema DoD for `feat` stories         |
| ADR-0017 | SAST toolchain — zero Critical/High enforced in `security` DoD      |
| ADR-0019 | CycloneDX SBOM — regenerated and scanned in `chore` and release DoD |
| ADR-0021 | OWASP LLM Top 10 — checklist in `feat` and `security` DoD           |
| ADR-0022 | Dependency pinning — hash pinning in `feat` and `chore` DoD         |
| ADR-0023 | HITL enforcement — agent action classification in `feat` DoD        |
| ADR-0025 | Kill-switch — drill cadence in release DoD                          |
| ADR-0026 | Bias audit — 90-day cadence in release DoD                          |
| ADR-0028 | PII sanitization — `sanitized=True` verification in `feat` DoD      |
| ADR-0029 | DPIA/RIPD — hard production release gate                            |

---

## References

- CLAUDE.md §2.1 SDD Cycle
- CLAUDE.md §5 RULE-001, RULE-C03, RULE-C04, RULE-005
- `specs/README.md` — spec ownership and review cadence
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — full gate list G01–G14
- `docs/adr/ADR-0008-test-coverage-thresholds.md` — coverage thresholds
