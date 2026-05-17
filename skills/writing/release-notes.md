# Skill: Release Notes

**Domain**: writing
**Activation triggers**: Release notes, CHANGELOG, SemVer, version bump, changelog entry, release, tag, Keep a Changelog
**References**: specs/sdlc/07-release-process.md, ADR-0006, CLAUDE.md §8 step 10

---

## Principles

- The `[Unreleased]` section of `CHANGELOG.md` is **managed automatically** by Release Please from Conventional Commits. Do not edit it manually (ADR-0006).
- Every CHANGELOG entry must reference the issue, ADR, or PR that produced the change.
- SemVer bump is derived from commit type — never from judgment calls.
- Language: English only (RULE-005).

---

## SemVer Bump Rules (ADR-0006)

| Commit type                  | Version bump | Example           |
| ---------------------------- | ------------ | ----------------- |
| `feat:` (new feature)        | **MINOR**    | `1.2.0` → `1.3.0` |
| `fix:`, `perf:`, `refactor:` | **PATCH**    | `1.2.0` → `1.2.1` |
| `BREAKING CHANGE:` footer    | **MAJOR**    | `1.2.0` → `2.0.0` |
| `docs:`, `chore:`, `test:`   | No bump      | Pre-release only  |
| `feat!:` or `fix!:` (bang)   | **MAJOR**    | `1.2.0` → `2.0.0` |

> Never bump MAJOR for security patches unless the fix changes the public API. File an ADR if unsure.

---

## Conventional Commit Format (Required for CHANGELOG automation)

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Types recognized by Release Please

| Type       | CHANGELOG category | Bumps version |
| ---------- | ------------------ | ------------- |
| `feat`     | Added              | MINOR         |
| `fix`      | Fixed              | PATCH         |
| `perf`     | Changed            | PATCH         |
| `refactor` | Changed            | PATCH         |
| `docs`     | —                  | No            |
| `chore`    | —                  | No            |
| `test`     | —                  | No            |
| `ci`       | —                  | No            |
| `security` | Security           | PATCH         |
| `revert`   | Removed            | PATCH         |

### Breaking change footer

```
feat(api): change approval endpoint response shape

BREAKING CHANGE: ApprovalToken response no longer includes `approver_name` field.
Callers must read the approver role from the audit trail instead.
```

### Scope examples for this project

| Scope           | Used for                               |
| --------------- | -------------------------------------- |
| `agents`        | Agent source code changes              |
| `guardrails`    | Guardrail pattern changes              |
| `api`           | HTTP API changes                       |
| `observability` | Logging, metrics, tracing changes      |
| `skills`        | Skills library additions/changes       |
| `specs`         | Spec additions/changes                 |
| `adr`           | New or superseded ADRs                 |
| `harness`       | Harness / CI configuration changes     |
| `infra`         | Terraform / Helm / monitoring changes  |
| `privacy`       | PII, LGPD, GDPR-related changes        |
| `security`      | Security controls, SAST rules, secrets |

---

## CHANGELOG Structure

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Traceability rule:** every entry must reference the issue, ADR or PR number.
> **Automation note:** the `[Unreleased]` section is managed automatically by
> [Release Please](https://github.com/googleapis/release-please). Do not edit it manually.

---

## [Unreleased]

### Added

### Changed

### Fixed

### Security

### Removed

---

## [1.2.0] — 2026-05-17

### Added

- `src/guardrails/kill_switch.py` — Vault credential revocation + pod termination; RTO < 60s (issue #23, ADR-0025)

### Fixed

- `src/adapters/inbound/alert_consumer.py` — Deduplication window was 3 min instead of 5 min (issue #27)
```

---

## Manual CHANGELOG Entry Rules

When Release Please does not auto-generate an entry (e.g. `docs:` commits) and the
change is significant enough to be in the changelog, add it to `[Unreleased]` manually
using this format:

```
- `<file or component>` — <one-sentence description of the change> (<issue #N> or <ADR-XXXX>)
```

Rules:

- One bullet per artifact or logical change unit.
- Always include the reference in parentheses at the end.
- No multi-sentence bullets — break into two entries if needed.
- Use the exact file path or component name, not a vague description.

---

## Release Process Checklist (from spec 07)

Before tagging a release:

- [ ] All CI gates green on `main`
- [ ] `[Unreleased]` section non-empty (Release Please populated it)
- [ ] SemVer bump matches the highest-impact commit type in this release window
- [ ] BREAKING CHANGE footer present if public API changed
- [ ] Bias audit report dated within 90 days (`release_gate_pass: true`)
- [ ] DPIA/RIPD gate not broken by this release (no new high-risk PII processing)
- [ ] SBOM generated and attached to GitHub Release asset
- [ ] SLSA provenance artifact attached to GitHub Release
- [ ] Blue-green deploy validated in staging before production cut-over
