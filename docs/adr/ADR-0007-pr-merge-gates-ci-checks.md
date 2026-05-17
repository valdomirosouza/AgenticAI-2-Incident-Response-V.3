# ADR-0007: PR Merge Gates — Mandatory CI Checks

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ4 (security, compliance)

---

## Context

`main` is the single long-lived branch (ADR-0005) and the deployment source. Any
defect, secret or security vulnerability merged to `main` is immediately in the
integration environment and potentially in the dissertation evaluation corpus.

SOC 2 CC8.1 (Change management) requires that changes to production systems pass
defined quality and security controls before deployment. The harness gates are the
technical implementation of this control.

Gates must be:

1. **Binary** — pass or block; no warnings promoted to errors later (CLAUDE.md §3).
2. **Exhaustive** — a PR that passes all gates can be merged with confidence.
3. **Listed explicitly** — every check that blocks merge must be named here so
   the harness configuration (issue #21) implements exactly this list.
4. **Traceable to a compliance requirement** — each gate exists because of a specific
   rule, regulation or quality standard.

## Decision

The following gates are **mandatory and blocking** on every PR targeting `main`.
A PR cannot be merged unless every gate returns a green status check.

### Gate set — PR Gate (`harness/code-check.yml`)

| #   | Gate                       | Tool                    | Blocks on                                          | Compliance driver               |
| --- | -------------------------- | ----------------------- | -------------------------------------------------- | ------------------------------- |
| G01 | SAST — Python              | Semgrep, Bandit         | Any Critical or High finding                       | PCI-DSS 6.3, CLAUDE.md RULE-C04 |
| G02 | SAST — IaC                 | Checkov                 | Any Critical finding in Terraform/Helm             | SOC 2 CC6                       |
| G03 | Secrets scan               | gitleaks, trufflehog    | Any credential, token or key detected              | RULE-C03, SOC 2 CC6.7           |
| G04 | Dependency CVE scan        | Trivy                   | Any Critical CVE in direct dependencies            | SLSA Level 2, PCI-DSS 6.3       |
| G05 | Unit tests                 | pytest                  | Any test failure; coverage < 80% on changed files  | ADR-0008                        |
| G06 | Integration tests          | pytest + testcontainers | Any test failure; coverage < 60% on changed paths  | ADR-0008                        |
| G07 | Import boundary check      | custom linter           | Any `domain/` import of `adapters/`                | ADR-0002                        |
| G08 | Conventional commit format | commit-check            | PR title does not match `type(scope): description` | ADR-0006                        |
| G09 | Doc gate — spec reference  | custom check            | PR has no linked spec in `specs/` (RULE-001)       | CLAUDE.md §3.1                  |
| G10 | PII static scan            | custom regex + Presidio | Any PII pattern in changed files (logs, fixtures)  | RULE-C03, GDPR Art. 25          |
| G11 | SBOM generation            | syft                    | SBOM file not generated or malformed               | SLSA Level 2                    |
| G12 | Licence compliance         | liccheck                | New dependency with incompatible licence           | Legal                           |
| G13 | Branch protection          | GitHub                  | Direct push to `main` without PR                   | ADR-0005                        |
| G14 | PR approval                | GitHub                  | PR merged without ≥ 1 approval                     | ADR-0005                        |

### Gate set — Documentation Gate (`harness/doc-check.yml`)

Triggered on changes to `docs/`, `specs/`, `skills/`, `CLAUDE.md`, `*.md`:

| #   | Gate                    | Check         | Blocks on                                           |
| --- | ----------------------- | ------------- | --------------------------------------------------- |
| D01 | Markdown lint           | markdownlint  | Style violations in changed `.md` files             |
| D02 | Dead link check         | lychee        | Any broken internal or external hyperlink           |
| D03 | Glossary consistency    | custom script | Term used in docs not present in `docs/glossary.md` |
| D04 | ADR template compliance | custom script | ADR missing any of the 8 mandatory sections         |

### Override policy

No gate may be bypassed without:

1. An ADR documenting the exception and its time-bound scope.
2. A comment in the PR explaining why the bypass is necessary.
3. Tech Lead approval (solo project: researcher self-approves with documented rationale).

`--no-verify`, `--admin` merge and gate suppression are logged in the audit trail.

## Alternatives Considered

| Alternative                             | Pros                                                          | Cons                                                                                  |
| --------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **No mandatory gates**                  | Zero friction                                                 | `main` becomes unreliable; SOC 2 CC8.1 violated; any secret exposure goes undetected  |
| **Gates as warnings only**              | Faster iteration                                              | Warnings are ignored; same outcome as no gates                                        |
| **Subset of gates (SAST + tests only)** | Reduced CI time                                               | Secrets and PII scans absent — highest-risk gaps left open                            |
| **Full gate set (14 PR + 4 doc)** ✅    | Complete coverage of quality, security, compliance dimensions | Higher CI time per PR — mitigated by parallelising jobs in `.github/workflows/ci.yml` |

## Consequences

**Positive:**

- SOC 2 CC8.1: every change to `main` passes a documented, auditable control set.
- Zero Critical/High SAST findings on `main` at all times — dissertation evaluation
  corpus is clean by construction.
- Secrets and PII never reach `main` — satisfies RULE-C03 and GDPR Art. 25
  (Privacy by Design).
- Gate list is the single source of truth for the harness configuration (issue #21) —
  no gap between policy and implementation.

**Negative / Trade-offs:**

- 14 gates increase CI wall time; mitigated by parallelisation in the workflow YAML.
- Custom gates (G07, G09, G10, D03, D04) must be authored — adds implementation work
  to Phase 4 (issue #21).
- Strict gate set may block a legitimate quick-fix; override policy (above) provides
  the escape hatch without removing the gate.

## Review Criteria

Revisit this decision if:

- CI wall time exceeds 15 minutes per PR — split gate set into fast (< 5 min) and
  slow (async, non-blocking for draft PRs) tiers.
- A gate consistently produces false positives (> 5% false positive rate over 30 PRs)
  — tune the tool configuration, not the gate policy.
- A new compliance requirement (e.g. ANPD guidance on AI systems) introduces a gate
  not covered here — add it and update this ADR.

## References

- SOC 2 Type II CC8.1 — Change management controls
- PCI-DSS v4.0 §6.3 — Identification and management of security vulnerabilities
- GDPR Art. 25 — Data protection by design and by default
- SLSA Level 2 — slsa.dev — provenance and build requirements
- `docs/adr/ADR-0005-trunk-based-development-branching.md` — branch protection (G13, G14)
- `docs/adr/ADR-0006-conventional-commits-semver.md` — commit format (G08)
- `docs/adr/ADR-0008-test-coverage-thresholds.md` — coverage thresholds (G05, G06)
- `harness/code-check.yml` — implementation of this gate set (to be authored, issue #21)
- CLAUDE.md §3 — Harness engineering principle
