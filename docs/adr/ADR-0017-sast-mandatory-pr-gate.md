# ADR-0017: SAST as Mandatory PR Gate — Zero Critical/High

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Security Lead — researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ4 (security compliance)

---

## Context

Static Application Security Testing (SAST) detects vulnerabilities in source code
before the code is executed. Applying SAST at the PR gate (rather than post-merge or
pre-release) follows the "shift-left" security principle: defects are cheapest to fix
when caught early, and security findings on `main` have a wider blast radius.

Requirements:

1. **Zero Critical/High findings to merge** — CLAUDE.md §1.6 criterion 3 is a hard
   project gate. Any Critical or High SAST finding must block merge and be resolved,
   not bypassed.
2. **Multiple tools** — no single SAST tool covers all vulnerability classes. A layered
   set of tools maximises coverage with acceptable false-positive rates.
3. **IaC coverage** — Terraform and Helm charts in `infrastructure/` are in scope;
   misconfigured cloud resources are a primary vulnerability class for cloud-native
   systems.
4. **Traceable to standards** — OWASP SAMM (Software Assurance Maturity Model) Level 2
   and PCI-DSS 6.3.2 both require automated SAST in the build/PR pipeline.

## Decision

SAST is a **mandatory, blocking** gate on every PR targeting `main` (gate G01/G02 in
ADR-0007). The following tools are the canonical SAST toolchain:

### SAST toolchain

| Tool        | Scope                   | What it detects                                                                               | Config file                 |
| ----------- | ----------------------- | --------------------------------------------------------------------------------------------- | --------------------------- |
| **Semgrep** | Python (`src/`)         | OWASP Top 10, custom rules for LLM/agent patterns, taint analysis                             | `harness/semgrep.yml`       |
| **Bandit**  | Python (`src/`)         | Python-specific: hardcoded secrets, insecure functions, SQL injection, shell injection        | `harness/bandit.ini`        |
| **CodeQL**  | Python (`src/`)         | Deep taint analysis, CWE coverage, complex multi-file vulnerabilities                         | `.github/codeql-config.yml` |
| **Checkov** | IaC (`infrastructure/`) | Terraform/Helm misconfigurations: public S3 buckets, open security groups, missing encryption | `harness/checkov.yml`       |

### Severity mapping and gate policy

| Severity     | Gate action                           | Resolution SLA                                             |
| ------------ | ------------------------------------- | ---------------------------------------------------------- |
| **Critical** | Blocks merge immediately              | Must be fixed before the PR can proceed                    |
| **High**     | Blocks merge                          | Must be fixed before the PR can proceed                    |
| **Medium**   | Warning only — logged, does not block | Must be addressed within 30 days (tracked as GitHub issue) |
| **Low**      | Informational                         | Best effort                                                |

The zero Critical/High policy applies to findings in changed files. Pre-existing
findings in unchanged files are tracked in a security backlog but do not block the PR.

### Custom Semgrep rules for Agentic AI

Custom Semgrep rules are maintained in `harness/semgrep-custom/` and cover:

- LLM01 (Prompt Injection): unsanitised input concatenated into LLM prompt string.
- Unsafe deserialization of agent action payloads.
- Missing HITL gate invocation before remediation action execution.
- PII field names in log statements (supplements gate G10).

### False positive management

SAST false positives are suppressed with inline `# nosec` (Bandit) or `# nosemgrep`
(Semgrep) annotations. Every suppression must include a comment explaining why the
finding is a false positive and reference an ADR or GitHub issue. Unexplained
suppressions block the PR (enforced by custom Semgrep rule).

## Alternatives Considered

| Alternative                                | Pros                                                                                                | Cons                                                                                                             |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Single tool (Bandit only)**              | Simple; fast                                                                                        | Limited to Python-specific patterns; no taint analysis; no IaC coverage                                          |
| **SonarQube**                              | Comprehensive; dashboard                                                                            | Requires server infrastructure; licensing cost; slower than CLI tools                                            |
| **Semgrep + Bandit + CodeQL + Checkov** ✅ | Complementary coverage: taint (CodeQL), patterns (Semgrep), Python-specific (Bandit), IaC (Checkov) | Four tools increase CI time — mitigated by parallelisation; false positives managed with suppression annotations |
| **No SAST**                                | Zero overhead                                                                                       | OWASP SAMM Level 2 not met; PCI-DSS 6.3.2 violated; Critical vulnerabilities reach `main`                        |

## Consequences

**Positive:**

- Zero Critical/High SAST findings on `main` by construction — CLAUDE.md §1.6
  criterion 3 satisfied at every commit.
- OWASP SAMM Level 2 (Security Testing practice): automated SAST in PR pipeline
  with documented tool set and severity thresholds.
- PCI-DSS 6.3.2: automated vulnerability scanning integrated into the development
  process with documented remediation SLAs.
- Custom Semgrep rules catch LLM-specific patterns not covered by generic SAST tools.

**Negative / Trade-offs:**

- Four SAST tools increase CI wall time by ~3–5 minutes; mitigated by running in
  parallel jobs in `.github/workflows/ci.yml`.
- CodeQL analysis is the slowest tool (~2–4 minutes for Python); can be moved to
  an async gate for draft PRs if iteration speed becomes an issue.
- Custom Semgrep rules require maintenance as agent patterns evolve; owned by the
  Security Lead.

## Review Criteria

Revisit this decision if:

- False positive rate across all tools exceeds 15% over 30 PRs — tune rules before
  adding more tools.
- A tool is deprecated or its licence changes incompatibly with the open dissertation
  replication package.
- GitHub Advanced Security (CodeQL) pricing changes make it unavailable for the
  research repository.

## References

- OWASP SAMM v2 — Software Assurance Maturity Model, Security Testing practice
- PCI-DSS v4.0 §6.3.2 — Automated technical security testing
- Semgrep — semgrep.dev; Bandit — bandit.readthedocs.io; CodeQL — codeql.github.com; Checkov — checkov.io
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — gates G01 and G02
- `docs/adr/ADR-0021-owasp-llm-top10-checklist.md` — custom Semgrep rules for LLM patterns
- `harness/code-check.yml` — SAST gate configuration (to be authored, issue #21)
- CLAUDE.md §1.6 criterion 3 — zero Critical/High SAST to merge
