# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Traceability rule:** every entry must reference the issue, ADR or PR that produced the change.
> **Automation note:** the `[Unreleased]` section is managed automatically by
> [Release Please](https://github.com/googleapis/release-please). Do not edit it manually.

---

## [Unreleased]

---

## [0.2.0-dev] — 2026-05-17

> Phase 0 bootstrap + Phase 1 ADR batch (issues #2–#6). Pre-automation record.
> From v0.2.0 onwards, Release Please generates changelog entries from Conventional Commits.

### Added

- `docs/adr/ADR-0016` – `ADR-0022` — DevSecOps & Security ADRs: STRIDE, SAST, DAST, SBOM, Vault, OWASP LLM Top 10, dependency pinning (issue #6, PR #30)
- `docs/adr/ADR-0011` – `ADR-0015` — Observability ADRs: Golden Signals, OpenTelemetry, JSON logging, PII masking, SLO alerting (issue #5, PR #29)
- `docs/adr/ADR-0005` – `ADR-0010` — SDLC & Engineering ADRs: trunk-based dev, Conventional Commits, PR gates, coverage thresholds, Blue-Green, blameless post-mortem (issue #4, PR #28)
- `docs/adr/ADR-0001` – `ADR-0004` — Architecture & Design ADRs: C4 Model, Hexagonal Architecture, LLM selection, multi-agent orchestration (issue #3, PR #27)
- Branch protection on `main`: PR required, 1 approval, no force-push (issue #2, PR #26)
- `.github/pull_request_template.md` with author and reviewer checklists (issue #2, PR #26)
- `docs/glossary.md` with canonical 53-term project glossary (issue #2, PR #26)
- `SECURITY.md` vulnerability disclosure policy (issue #2, PR #26)
- `PRIVACY.md` data processing notice — LGPD art. 48, GDPR art. 33 (issue #2, PR #26)

---

## [0.1.0] — 2026-05-17

### Added

- `CLAUDE.md` v1.2.0 — behavioral contract for Claude Code: 8-pillar architecture, SDD cycle,
  harness rules, skill activation table, canonical glossary, 10-step workflow (PR #1-equivalent)
- `specs/README.md` — spec hierarchy: 22 spec files across 6 domains with per-file descriptions
- `docs/adr/README.md` — canonical ADR template + index of all 32 foundational ADRs
- `docs/repo-structure.md` — full annotated directory tree
- `skills/README.md` — 12 enterprise-grade shared skills library
- `skills/project-skills-catalog.md` — catalog of 30+ planned project-specific skills
- `issues.md` — 24-issue implementation backlog organized in 6 phases with dependency graph
- `README.md` — full project description: problem statement, solution, architecture, roadmap
- GitHub Issues #2–#25 — 24 documented issues with acceptance criteria and cross-references
- GitHub Milestones — 6 milestones (one per implementation phase)
- GitHub Labels — 14 labels (`phase:`, `type:`, `priority:`)
- `.github/workflows/` — Claude Code Review and Claude PR Assistant workflows (PR #1)
