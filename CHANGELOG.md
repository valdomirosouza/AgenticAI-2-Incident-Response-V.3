# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Traceability rule:** every entry must reference the issue, ADR or PR that produced the change.

---

## [Unreleased]

### Added

- `docs/adr/ADR-0005-trunk-based-development-branching.md` — Trunk-based development with short-lived feature branches (issue #4)
- `docs/adr/ADR-0006-conventional-commits-semver.md` — Conventional Commits v1.0.0 + SemVer 2.0.0 (issue #4)
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — 14 mandatory PR gate checks + 4 doc gates (issue #4)
- `docs/adr/ADR-0008-test-coverage-thresholds.md` — Tiered coverage: 95% guardrails, 90% domain, 80% overall (issue #4)
- `docs/adr/ADR-0009-blue-green-deployment-strategy.md` — Blue-Green deployment with < 30s rollback SLA (issue #4)
- `docs/adr/ADR-0010-blameless-post-mortem-format.md` — Blameless 8-section post-mortem as mandatory format (issue #4)
- `docs/adr/ADR-0001-c4-model-architecture-documentation.md` — C4 Model adopted for all architecture diagrams (issue #3)
- `docs/adr/ADR-0002-hexagonal-architecture-agent-services.md` — Hexagonal Architecture (Ports & Adapters) for all agent services (issue #3)
- `docs/adr/ADR-0003-llm-provider-model-selection.md` — Anthropic Claude Sonnet 4.6 selected as primary LLM (issue #3)
- `docs/adr/ADR-0004-multi-agent-orchestration-pattern.md` — Orchestrator + Specialists pattern with HITL/HOTL autonomy enforcement (issue #3)
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
