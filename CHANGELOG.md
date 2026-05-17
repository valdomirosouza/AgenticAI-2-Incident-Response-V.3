# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Traceability rule:** every entry must reference the issue, ADR or PR that produced the change.

---

## [Unreleased]

### Added

- `docs/adr/ADR-0016-stride-threat-modeling-method.md` — STRIDE + LLM extensions as mandatory threat modeling method (issue #6)
- `docs/adr/ADR-0017-sast-mandatory-pr-gate.md` — Semgrep + Bandit + CodeQL + Checkov; zero Critical/High to merge (issue #6)
- `docs/adr/ADR-0018-dast-staging-before-release.md` — OWASP ZAP + Nuclei in staging gate before every release (issue #6)
- `docs/adr/ADR-0019-cyclonedx-sbom-per-build.md` — CycloneDX v1.6 SBOM via Syft on every build; Grype CVE gate (issue #6)
- `docs/adr/ADR-0020-zero-trust-secrets-management.md` — HashiCorp Vault with AppRole auth; no secrets in env vars or git (issue #6)
- `docs/adr/ADR-0021-owasp-llm-top10-checklist.md` — Full OWASP LLM Top 10 mitigations for all Agentic AI components (issue #6)
- `docs/adr/ADR-0022-dependency-pinning-cve-scanning.md` — pip-compile hash pinning + Grype/Trivy CVE scanning (issue #6)
- `docs/adr/ADR-0011-golden-signals-canonical-metric-set.md` — Four Golden Signals as canonical metric set for all service monitoring (issue #5)
- `docs/adr/ADR-0012-opentelemetry-instrumentation-standard.md` — OpenTelemetry as unified instrumentation standard; W3C TraceContext propagation (issue #5)
- `docs/adr/ADR-0013-structured-json-logging-schema.md` — Structured JSON logging with 11 mandatory fields including trace_id and span_id (issue #5)
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md` — PII masking enforced at application layer + OTel Collector before ingestion (issue #5)
- `docs/adr/ADR-0015-slo-based-alerting-thresholds.md` — Multi-window multi-burn-rate SLO alerting; MTTD < 5 min for P1 (issue #5)
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
