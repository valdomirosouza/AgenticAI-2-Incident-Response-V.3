# Security Policy

## Supported Versions

This is an active research and dissertation project. The following versions receive security attention:

| Version          | Supported |
| ---------------- | --------- |
| `main` (latest)  | Yes       |
| Any other branch | No        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in this project, report it responsibly:

**Contact:** valdomirojr@gmail.com
**Subject line:** `[SECURITY] AgenticAI-2-Incident-Response — <brief description>`

### What to Include

- A clear description of the vulnerability and its potential impact
- Steps to reproduce (proof of concept, if available)
- Affected component(s): `src/agents/`, `src/guardrails/`, `src/api/`, etc.
- Any suggested mitigation or fix

### Response Timeline

| Stage                                  | Target SLA                       |
| -------------------------------------- | -------------------------------- |
| Acknowledgement                        | Within 48 hours                  |
| Initial assessment                     | Within 5 business days           |
| Resolution or risk-acceptance decision | Within 30 days for Critical/High |

### Severity Classification

Findings are classified following the harness SAST policy (`harness/code-check.yml`):

| Severity     | Definition                                                    | Resolution SLA  |
| ------------ | ------------------------------------------------------------- | --------------- |
| **Critical** | Remote code execution, credential exposure, data exfiltration | 24 hours        |
| **High**     | Privilege escalation, HITL bypass, PII disclosure             | 5 business days |
| **Medium**   | Logic flaws, misconfiguration, information leakage            | 30 days         |
| **Low**      | Minor issues, hardening opportunities                         | Best effort     |

## Security Controls in Place

This project enforces the following security controls (governed by ADRs once authored):

- **SAST** — Semgrep, Bandit, CodeQL on every PR (zero Critical/High to merge)
- **Secrets scanning** — gitleaks, trufflehog on every commit
- **DAST** — OWASP ZAP in staging before every production release
- **SBOM** — CycloneDX generated on every build
- **Dependency scanning** — Trivy/Grype, zero Critical CVEs to deploy
- **OWASP LLM Top 10** — checklist applied to all Agentic AI components
- **HITL** — all autonomous production remediation requires human approval

## Scope

| In scope                                      | Out of scope                               |
| --------------------------------------------- | ------------------------------------------ |
| Source code in `src/`                         | Third-party dependencies (report upstream) |
| API endpoints in `src/api/`                   | GitHub Actions infrastructure              |
| Agent guardrails in `src/guardrails/`         | Academic research methodology              |
| Observability pipeline (`src/observability/`) |                                            |

## Disclosure Policy

This project follows **responsible disclosure**. Once a fix is confirmed and deployed, the vulnerability will be documented in `CHANGELOG.md` under the `Security` category with the CVE or internal reference, if applicable.

---

_Governed by ADR-0020 (Zero-trust secrets management) and ADR-0017 (SAST mandatory PR gate) — to be authored in Phase 1._
