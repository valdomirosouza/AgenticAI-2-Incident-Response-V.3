# Spec 06: PR and Review Process

**Domain**: sdlc
**Owner**: Engineering Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #10
**Linked ADRs**: ADR-0007
**Review cadence**: Quarterly or on CI gate change

---

## 1. Purpose

Define the pull request lifecycle, CI gate requirements, reviewer assignment rules and
approval thresholds that govern every merge into `main`.

---

## 2. Context

ADR-0007 established 14 binary PR gates (G01–G14) and 4 documentation gates (D01–D04).
This spec translates those gates into the human process: who opens PRs, what they must
include, who reviews, what reviewers check, and what the merge ceremony looks like.

---

## 3. Decision

### 3.1 PR creation checklist (author obligations)

Every PR must include before requesting review:

- [ ] **Title**: Conventional Commit format — `<type>(<scope>): <description>` (ADR-0006)
- [ ] **Issue link**: `Closes #<N>` in the PR body
- [ ] **Spec reference**: link to the spec that governs the change (RULE-001)
- [ ] **ADR reference**: link to any ADR created or modified by this change
- [ ] **Self-review**: author has read their own diff before requesting review
- [ ] **Tests**: new tests cover the change; `pytest` passes locally
- [ ] **No secrets**: no credentials, API keys or PII in any committed file (RULE-C03)
- [ ] **Branch up to date**: rebased on `main` before opening; no merge commits

### 3.2 CI gate definitions

All gates are binary and blocking. A gate failure blocks merge — no exceptions without
a new ADR documenting the waiver.

#### Code gates (G01–G14)

| Gate | Check                     | Tool                             | Threshold                                                |
| ---- | ------------------------- | -------------------------------- | -------------------------------------------------------- |
| G01  | Unit + integration tests  | pytest                           | All pass; zero failures                                  |
| G02  | Branch coverage           | pytest-cov `--cov-branch`        | ≥ 80% overall; ≥ 90% domain; ≥ 95% guardrails (ADR-0008) |
| G03  | Static analysis — Python  | Semgrep + Bandit                 | Zero Critical/High findings                              |
| G04  | Static analysis — general | CodeQL                           | Zero Critical/High findings                              |
| G05  | IaC security              | Checkov                          | Zero Critical/High findings                              |
| G06  | Secret scanning           | Gitleaks                         | Zero detected secrets                                    |
| G07  | Dependency CVE scan       | Grype                            | Zero Critical CVEs; zero unmitigated High CVEs           |
| G08  | SBOM generation           | Syft (CycloneDX v1.6)            | SBOM artifact produced and attached (ADR-0019)           |
| G09  | Import linter             | import-linter                    | Zero hexagonal layer violations (ADR-0002)               |
| G10  | Type checking             | mypy `--strict`                  | Zero type errors                                         |
| G11  | LLM sanitization rule     | Semgrep `llm-unsanitized-prompt` | Zero violations (ADR-0028)                               |
| G12  | Conventional Commit title | commitlint                       | PR title matches pattern                                 |
| G13  | Dependency hash pinning   | pip-audit                        | All requirements hash-pinned (ADR-0022)                  |
| G14  | Docker image scan         | Trivy                            | Zero Critical CVEs in base image                         |

#### Documentation gates (D01–D04)

| Gate | Check                   | Threshold                                                                             |
| ---- | ----------------------- | ------------------------------------------------------------------------------------- |
| D01  | Markdown lint           | Zero errors (markdownlint)                                                            |
| D02  | Broken links            | Zero broken internal links                                                            |
| D03  | Spec mandatory sections | All 5 sections present (Purpose, Context, Decision, Acceptance Criteria, Linked ADRs) |
| D04  | ADR status field        | Status is one of: Proposed, Accepted, Deprecated, Superseded                          |

### 3.3 Reviewer assignment

| PR type           | Required reviewers                       | Minimum approvals |
| ----------------- | ---------------------------------------- | ----------------- |
| `feat` — domain   | Tech Lead                                | 1                 |
| `feat` — adapters | Tech Lead + SRE Lead                     | 1                 |
| `security`        | Security Lead + Tech Lead                | 1                 |
| `fix`             | Tech Lead or Engineering Lead            | 1                 |
| `docs` / `chore`  | Tech Lead                                | 1                 |
| `hotfix`          | Tech Lead (async; admin merge permitted) | 1 (async)         |
| **ADR change**    | Tech Lead + domain owner                 | 1                 |
| **Privacy spec**  | DPO / Privacy Lead + Tech Lead           | 1                 |

For solo project: all reviews fulfilled by Tech Lead (Valdomiro) with admin bypass.

### 3.4 Reviewer obligations

A reviewer approves only when they have verified:

- [ ] The change matches the linked spec and ADR (no undocumented deviations)
- [ ] Tests are meaningful — they test behaviour, not implementation detail
- [ ] No obvious security anti-patterns (OWASP Top 10 / LLM Top 10 applicable to the change)
- [ ] Observability: logs and traces are present for the new code paths
- [ ] Privacy: no new PII categories introduced without updating `specs/privacy/19-pii-inventory.md`
- [ ] All CI gates (G01–G14, D01–D04 if applicable) are green

### 3.5 PR merge ceremony

1. All CI gates green.
2. Required approvals received.
3. Branch up to date with `main` (rebase if needed).
4. **Squash merge** — one commit per PR on `main`; squash commit message = PR title.
5. Delete branch immediately after merge (`--delete-branch`).
6. Release Please picks up the Conventional Commit message and updates `[Unreleased]`.

### 3.6 PR size guidance

| PR type    | Recommended line change | Max before split required |
| ---------- | ----------------------- | ------------------------- |
| `feat`     | < 400 lines             | 800 lines                 |
| `fix`      | < 200 lines             | 400 lines                 |
| `security` | < 300 lines             | 600 lines                 |
| `docs`     | < 600 lines             | 1 200 lines               |
| `chore`    | < 200 lines             | 400 lines                 |

PRs exceeding the max are split into smaller PRs unless a waiver is granted by the
Tech Lead with documented rationale in the PR description.

---

## 4. Acceptance Criteria

- [ ] PR creation checklist covers 8 mandatory author items
- [ ] All 14 code gates (G01–G14) are listed with tool and threshold
- [ ] All 4 documentation gates (D01–D04) are listed
- [ ] Reviewer assignment table covers all PR types including ADR changes and privacy specs
- [ ] Reviewer obligations checklist covers: spec match, test quality, security, observability, privacy
- [ ] Merge ceremony mandates squash merge and branch deletion
- [ ] PR size guidance defines max before split for each PR type
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                      |
| -------- | -------------------------------------------------------------- |
| ADR-0002 | Hexagonal architecture — import linter gate G09                |
| ADR-0006 | Conventional Commits — PR title format requirement             |
| ADR-0007 | PR merge gates — G01–G14 and D01–D04 authoritative definitions |
| ADR-0008 | Test coverage thresholds — gate G02 thresholds                 |
| ADR-0017 | SAST toolchain — gates G03, G04, G05                           |
| ADR-0019 | CycloneDX SBOM — gate G08                                      |
| ADR-0022 | Dependency pinning — gate G13                                  |
| ADR-0028 | PII sanitization — gate G11 (Semgrep custom rule)              |

---

## References

- CLAUDE.md §2.1 SDD Cycle
- CLAUDE.md §5 RULE-001, RULE-C03, RULE-C04
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md`
- `.github/pull_request_template.md` — PR template with author + reviewer checklists
- `specs/sdlc/04-definition-of-done.md` — DoD per story type
- `specs/sdlc/05-branching-strategy.md` — branch naming and lifecycle
