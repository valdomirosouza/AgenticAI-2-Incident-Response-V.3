# Spec 13: SAST / DAST Policy

**Domain**: security
**Owner**: Security Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #12
**Linked ADRs**: ADR-0017, ADR-0018
**Review cadence**: Every release + on new tool adoption

---

## 1. Purpose

Define the static and dynamic analysis toolchain, scan frequency, severity thresholds
and remediation SLAs that govern every PR and every release.

---

## 2. Context

ADR-0017 mandated Semgrep + Bandit + CodeQL + Checkov as the SAST toolchain with zero
Critical/High findings to merge. ADR-0018 mandated OWASP ZAP + Nuclei as the DAST
toolchain run against staging before every release. This spec translates both ADRs into
operational policy: what runs when, who owns remediation, and what the SLA is.

---

## 3. Decision

### 3.1 SAST toolchain

| Tool    | Target                        | Trigger        | Config file                 | Blocks merge? |
| ------- | ----------------------------- | -------------- | --------------------------- | ------------- |
| Semgrep | Python source                 | Every PR (G03) | `harness/semgrep.yml`       | Yes           |
| Bandit  | Python source                 | Every PR (G03) | `harness/bandit.ini`        | Yes           |
| CodeQL  | Python + YAML                 | Every PR (G04) | `.github/codeql-config.yml` | Yes           |
| Checkov | Terraform + Helm + GH Actions | Every PR (G05) | `harness/checkov.yml`       | Yes           |

All SAST tools run in the PR gate CI job (`harness/code-check.yml`). Results are
uploaded as SARIF to GitHub Advanced Security for triage visibility.

#### Custom Semgrep rules (project-specific)

| Rule ID                  | What it detects                                           | ADR      |
| ------------------------ | --------------------------------------------------------- | -------- |
| `llm-unsanitized-prompt` | `llm_adapter.complete()` called without `sanitized=True`  | ADR-0028 |
| `hitl-bypass`            | `action_executor.execute()` without `ApprovalToken` param | ADR-0023 |
| `secret-in-env`          | `os.environ` or `os.getenv` used to read secrets          | ADR-0020 |
| `raw-log-pii`            | Logging statements referencing `user_id`, `email`, `ip`   | ADR-0014 |

Custom rules are maintained in `harness/semgrep-rules/` and pinned by SHA in CI.

### 3.2 DAST toolchain

| Tool      | Target      | Trigger      | Config file                 | Blocks release? |
| --------- | ----------- | ------------ | --------------------------- | --------------- |
| OWASP ZAP | Staging API | Staging gate | `harness/zap-baseline.conf` | Yes             |
| Nuclei    | Staging API | Staging gate | `harness/nuclei-templates/` | Yes             |

DAST runs in the staging gate (`harness/staging-check.yml`) after every deploy to
staging. A dedicated read-only service account (`dast-scanner@copilot.svc`) with no
write permissions is used for authenticated scans — it cannot execute HITL approvals
or trigger remediation actions.

OWASP ZAP scan types:

- **Baseline scan** (passive, ~5 min): runs on every staging deploy.
- **Active scan** (active, ~30 min): runs weekly on staging and before every release.

### 3.3 Severity thresholds

| Severity     | SAST: blocks PR merge? | DAST: blocks release? | Remediation SLA           |
| ------------ | ---------------------- | --------------------- | ------------------------- |
| **Critical** | Yes — immediate block  | Yes — immediate block | **24 hours**              |
| **High**     | Yes — immediate block  | Yes — immediate block | **5 business days**       |
| **Medium**   | No — warning in CI     | No — warning in PR    | **30 days**               |
| **Low**      | No — informational     | No — informational    | Next sprint (best effort) |
| **Info**     | No                     | No                    | No obligation             |

SLA clock starts at the time the finding is first reported in the GitHub Security tab.
The finding owner is the PR author for SAST; the SRE Lead for DAST findings.

### 3.4 Finding triage process

```
Finding detected by SAST/DAST
        │
        ▼
Is severity Critical or High?
  YES → PR/release blocked immediately
        └─ Author notified via CI annotation + GitHub Security alert
        └─ SLA clock starts (24h Critical / 5bd High)
        └─ Fix, reopen PR → re-run SAST gate
  NO (Medium/Low) → Warning annotation in CI
        └─ Ticket created automatically via GitHub Issue (label: security)
        └─ Assigned to PR author
        └─ Tracked in next sprint planning
```

### 3.5 False positive process

A SAST finding may be marked as false positive if:

1. The author documents the rationale in the PR description (not a code comment).
2. Security Lead acknowledges the false positive in a PR review comment.
3. A Semgrep `nosemgrep: <rule-id>` comment is added inline with the rationale.
4. The exemption is logged as a GitHub Security alert dismissal with reason.

No blanket `nosemgrep` suppressions — each is per-line and documented.

### 3.6 OWASP LLM Top 10 manual checklist

In addition to automated SAST, every PR touching LLM integration paths must include a
manual OWASP LLM Top 10 (2025) checklist review (ADR-0021):

| Item  | Check                                                           | Gate        |
| ----- | --------------------------------------------------------------- | ----------- |
| LLM01 | Prompt injection: new inputs sanitized before LLM dispatch      | PR author   |
| LLM02 | Insecure output handling: response validated by Pydantic        | PR author   |
| LLM05 | Improper output handling: schema failure → escalate, not ignore | Code review |
| LLM06 | Excessive agency: no new autonomous PRODUCTION\_\* path added   | Code review |
| LLM09 | Overreliance: confidence threshold ≥ 0.6 enforced               | Code review |

The checklist is embedded in `.github/pull_request_template.md` and must be checked
before the PR is submitted.

### 3.7 Scan result retention

SAST SARIF results are retained in GitHub Advanced Security for the lifetime of the
repository. DAST scan reports (ZAP HTML + Nuclei JSON) are stored as GitHub Actions
artifacts with a 90-day TTL (ADR-0030).

---

## 4. Acceptance Criteria

- [ ] SAST table covers all 4 tools with config file and gate reference
- [ ] Custom Semgrep rules listed: `llm-unsanitized-prompt`, `hitl-bypass`, `secret-in-env`, `raw-log-pii`
- [ ] DAST table covers ZAP (baseline + active) and Nuclei with authenticated scan account
- [ ] Remediation SLA defined: Critical = 24h, High = 5 business days, Medium = 30 days
- [ ] Finding triage process documented for both blocking and non-blocking severities
- [ ] False positive process requires Security Lead acknowledgement — no self-service suppression
- [ ] OWASP LLM Top 10 manual checklist covers LLM01, LLM02, LLM05, LLM06, LLM09
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                              |
| -------- | ---------------------------------------------------------------------- |
| ADR-0007 | PR merge gates — G03 (SAST), G04 (CodeQL), G05 (Checkov)               |
| ADR-0014 | PII masking — `raw-log-pii` Semgrep rule enforces it                   |
| ADR-0017 | SAST mandatory PR gate — toolchain selection and thresholds            |
| ADR-0018 | DAST staging gate — ZAP + Nuclei config                                |
| ADR-0020 | Vault — `secret-in-env` Semgrep rule enforces no env-var secrets       |
| ADR-0021 | OWASP LLM Top 10 — manual checklist items LLM01–LLM09                  |
| ADR-0023 | HITL enforcement — `hitl-bypass` Semgrep rule enforces token gate      |
| ADR-0028 | PII sanitization — `llm-unsanitized-prompt` Semgrep rule enforces gate |

---

## References

- CLAUDE.md §1.5 Compliance Baseline (OWASP LLM Top 10, PCI-DSS 6.3, SOC 2)
- `docs/adr/ADR-0017-sast-mandatory-pr-gate.md`
- `docs/adr/ADR-0018-dast-staging-before-release.md`
- `docs/adr/ADR-0021-owasp-llm-top10-checklist.md`
- `specs/security/12-threat-model.md` — threat register that SAST/DAST findings trace back to
- `specs/sdlc/06-pr-and-review-process.md` — G03–G05 gate definitions
