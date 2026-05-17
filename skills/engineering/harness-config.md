# Skill: Harness Configuration

**Domain**: engineering
**Activation triggers**: Harness, CI gate, harness configuration, harness check, code gate, PR gate, release gate, doc gate, staging gate, harness YAML, check rules
**References**: harness/, CLAUDE.md §3, ADR-0007, ADR-0008, specs/sdlc/06-pr-and-review-process.md

---

## Harness Overview

The harness is the automated verification layer that enforces quality, security and
consistency gates. Gates are **binary** — pass or block. No warnings promoted to errors
later, no manual overrides without an ADR (CLAUDE.md §3).

---

## Four Harness Files

| File                        | Trigger                           | Blocks            |
| --------------------------- | --------------------------------- | ----------------- |
| `harness/code-check.yml`    | Every pull request                | Merge             |
| `harness/staging-check.yml` | Post-deploy to staging            | Production deploy |
| `harness/release-check.yml` | Pre-deploy to production          | Release           |
| `harness/doc-check.yml`     | Changes to docs/, specs/, skills/ | Merge             |

---

## PR Gate (code-check.yml) — 14 Code Gates + 4 Doc Gates

### Code gates (G01–G14)

| Gate | Check                                    | Tool                      | Failure action        |
| ---- | ---------------------------------------- | ------------------------- | --------------------- |
| G01  | Unit test coverage ≥ 80%                 | pytest-cov                | Block merge           |
| G02  | Integration test coverage ≥ 60%          | pytest-cov                | Block merge           |
| G03  | Guardrails coverage ≥ 95% branch         | pytest-cov                | Block merge           |
| G04  | Zero Critical SAST findings              | Semgrep + Bandit + CodeQL | Block merge           |
| G05  | Zero High SAST findings                  | Semgrep + Bandit          | Block merge           |
| G06  | Custom rule: `llm-unsanitized-prompt`    | Semgrep                   | Block merge           |
| G07  | Custom rule: `hitl-bypass`               | Semgrep                   | Block merge           |
| G08  | Custom rule: `secret-in-env`             | Semgrep                   | Block merge           |
| G09  | Custom rule: `raw-log-pii`               | Semgrep                   | Block merge           |
| G10  | Zero exposed secrets                     | Gitleaks                  | Block merge           |
| G11  | Zero Critical CVEs in dependencies       | pip-audit                 | Block merge (24h SLA) |
| G12  | Pydantic schema validation on all models | mypy + pydantic validator | Block merge           |
| G13  | Import layer rules (hexagonal arch)      | import-linter             | Block merge           |
| G14  | Conventional Commit format               | commitlint                | Block merge           |

### Doc gates (D01–D04)

| Gate | Check                                         | Tool               | Failure action |
| ---- | --------------------------------------------- | ------------------ | -------------- |
| D01  | All spec files have 5 mandatory sections      | mdlint custom rule | Block merge    |
| D02  | All ADR files have Status field               | grep / lint        | Block merge    |
| D03  | No real PII in docs, specs, or skills files   | Presidio scan      | Block merge    |
| D04  | No secrets or real hostnames in documentation | Gitleaks + grep    | Block merge    |

---

## Staging Gate (staging-check.yml)

Runs after every successful deploy to the staging environment. Blocks production deploy.

| Check                                     | Tool                 | Threshold                            |
| ----------------------------------------- | -------------------- | ------------------------------------ |
| DAST baseline scan                        | OWASP ZAP            | Zero Critical/High findings          |
| DAST active scan (staging only)           | OWASP ZAP            | Zero Critical findings               |
| Nuclei CVE probe                          | Nuclei               | Zero Critical template matches       |
| SLO smoke test (Golden Signals for 5 min) | k6 + Prometheus      | All SLIs within SLO targets          |
| Audit trail write test                    | pytest (e2e)         | 100% write success                   |
| HITL gate end-to-end test                 | pytest (e2e)         | ApprovalToken validated and executed |
| PII sanitizer integration test            | pytest (integration) | Zero PII in LLM prompt fixture       |
| Kill-switch drill                         | pytest (e2e)         | Pod terminates in < 10s              |

---

## Release Gate (release-check.yml)

Runs before every production deploy. Blocks release.

| Check                                        | Required state                                                          |
| -------------------------------------------- | ----------------------------------------------------------------------- |
| All PR gate checks green on `main`           | Latest CI run green                                                     |
| All staging gate checks green                | Latest staging run green                                                |
| SBOM generated (CycloneDX v1.6)              | `sbom.json` artifact attached to GitHub Release                         |
| SLSA provenance artifact present             | Cosign-signed provenance attached to GitHub Release                     |
| Bias audit report current (≤ 90 days)        | `release_gate_pass: true` in most recent `bias-audit-report-*.json`     |
| DPIA/RIPD gate                               | `specs/privacy/21-dpia-ripd.md` status Approved + DPO signature present |
| Zero unmitigated Critical/High SAST findings | Security scan on tagged commit clean                                    |
| Anonymization report current (≤ 6 months)    | All referenced evaluation corpora have `overall_pass: true`             |
| Blue-green smoke test in staging             | 100% traffic shifted, zero error budget burned                          |

---

## Doc Gate (doc-check.yml)

Triggered on any PR that modifies `docs/`, `specs/`, or `skills/`.

```yaml
# harness/doc-check.yml (structure reference)
checks:
  - id: D01
    name: spec-mandatory-sections
    pattern: "specs/**/*.md"
    required_headings:
      - "## 1. Purpose"
      - "## 2. Context"
      - "## 3. Decision"
      - "## 4. Acceptance Criteria"
      - "## 5. Linked ADRs"

  - id: D02
    name: adr-status-field
    pattern: "docs/adr/ADR-*.md"
    required_pattern: "\\*\\*Status\\*\\*:"

  - id: D03
    name: no-pii-in-docs
    tool: presidio-scan
    languages: [en, pt]
    confidence_threshold: 0.7
    action: block

  - id: D04
    name: no-secrets-in-docs
    tool: gitleaks
    config: .gitleaks.toml
    action: block
```

---

## Adding or Modifying a Gate

1. **Write an ADR first.** Any gate change that affects merge or release criteria requires an ADR (ADR-0007 governs all PR gates).
2. Create or update the relevant harness YAML under `harness/`.
3. Update the corresponding CI workflow in `.github/workflows/` to reference the harness file.
4. Add a test in `tests/harness/` that verifies the gate fires on a known-failing fixture.
5. Open a PR with both the harness YAML and the ADR.

---

## Semgrep Custom Rules (ADR-0017)

Custom rules live in `.semgrep/` at the repo root.

| Rule ID                  | Pattern detected                                        | Gate |
| ------------------------ | ------------------------------------------------------- | ---- |
| `llm-unsanitized-prompt` | `LLMAdapter.complete()` called without `sanitized=True` | G06  |
| `hitl-bypass`            | `adapter.execute()` called outside `action_executor`    | G07  |
| `secret-in-env`          | Hard-coded credential pattern in any `.py` or `.env`    | G08  |
| `raw-log-pii`            | `logger.*` call with raw user input (no masking call)   | G09  |

New rules must follow the Semgrep YAML format and include a `fix:` suggestion.
Semgrep rule PRs require Security Lead review.

---

## False Positive Process (from spec 13)

1. Engineer flags finding as FP in PR comment with justification.
2. Security Lead reviews within 2 business days.
3. If accepted: finding added to `.semgrep-ignore` with expiry date (max 90 days).
4. If rejected: engineer must fix the finding before merge.
5. All FP decisions are logged in `docs/security/false-positives.md`.

No finding may be suppressed without Security Lead approval. `// nosemgrep` inline suppressions are prohibited except in test fixtures.
