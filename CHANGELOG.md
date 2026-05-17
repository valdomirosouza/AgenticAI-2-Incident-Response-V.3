# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Traceability rule:** every entry must reference the issue, ADR or PR that produced the change.

---

## [Unreleased]

### Added

- Branch protection on `main`: PR required, 1 approval, no force-push (issue #2)
- `.github/pull_request_template.md` with author and reviewer checklists (issue #2)
- `docs/glossary.md` with canonical project glossary (issue #2)
- `SECURITY.md` vulnerability disclosure policy (issue #2)
- `PRIVACY.md` data processing notice — LGPD art. 48, GDPR art. 33 (issue #2)

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
