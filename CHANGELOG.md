# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Traceability rule:** every entry must reference the issue, ADR or PR that produced the change.
> **Automation note:** the `[Unreleased]` section is managed automatically by
> [Release Please](https://github.com/googleapis/release-please). Do not edit it manually.

---

## [Unreleased]

### Added

- `skills/domain/agentic-ai-taxonomy.md` — Canonical definitions table; autonomy spectrum diagram; perception-action loop; multi-agent architecture patterns; HITL/HOTL decision heuristics; common mistakes (issue #15)
- `skills/domain/incident-lifecycle.md` — T0–T5 lifecycle diagram; per-stage agent ownership and autonomy mode; escalation rules; MTTD/MTTR measurement points; quantitative targets per severity (issue #15)
- `skills/domain/mttd-mttr-metrics.md` — MTTD/MTTR/MTTI/MTTF definitions; formulas; 6 ABNT-cited industry benchmarks; Prometheus recording rules; Python compute functions; statistical considerations (issue #15)
- `skills/domain/guardrails-patterns.md` — 6 guardrail patterns with Python code (HITL gate, HOTL hook, PII sanitizer, schema validator, kill-switch, confidence threshold); composition pipeline; test requirements table (issue #15)
- `specs/privacy/19-pii-inventory.md` — 10 PII categories; Data Flow Diagram; masking rules for logs/traces/LLM prompts; legal basis per category (issue #14)
- `specs/privacy/20-data-retention-policy.md` — 11-category TTL schedule; backend config map; LLM prompt non-persistence; 7-step erasure procedure; audit evidence requirements (issue #14)
- `specs/privacy/21-dpia-ripd.md` — Full DPIA/RIPD (Parts A–F); 10-risk register; DPO sign-off 2026-05-17; LGPD legitimate interest assessment; hard gate completion checklist (issue #14)
- `specs/privacy/22-anonymization-standard.md` — 6-dataset technique selection; 5-step pipeline; k≥5/risk<5%/utility≥80% gates; DP ε=1.0; ARX journalist attack test; report schema (issue #14)
- `specs/ethics/16-autonomy-boundaries.md` — Full action-type × autonomy matrix; HITL timeout protocol; ApprovalToken schema; BLOCKED enforcement layers; EU AI Act Art. 14 compliance (issue #13)
- `specs/ethics/17-audit-trail.md` — 12-field event schema; 22-event vocabulary; SHA-256 hash chain; WORM storage; access control; 2-year retention; erasure procedure (issue #13)
- `specs/ethics/18-bias-audit-plan.md` — 4 bias metrics (SCER, CV_MTTD, RCRR, KL_drift); Fairlearn tooling; quarterly cadence; remediation criteria; kill-switch drill (issue #13)
- `specs/security/12-threat-model.md` — STRIDE register (20 threats) across 4 components; trust boundary map; residual risk register (issue #12)
- `specs/security/13-sast-dast-policy.md` — SAST toolchain (Semgrep/Bandit/CodeQL/Checkov) + 4 custom rules; DAST (ZAP+Nuclei); remediation SLAs; false-positive process (issue #12)
- `specs/security/14-secrets-management.md` — 8-secret catalogue; Vault policies; rotation schedule; 8-step emergency revocation (RTO < 30s) (issue #12)
- `specs/security/15-supply-chain-policy.md` — CycloneDX SBOM; hash pinning rules; CVE triage SLA; license allowlist/prohibited list; SLSA Level 2 evidence (issue #12)
- `specs/observability/08-golden-signals.md` — p50/p95/p99 targets per service tier; LLM latency metric; error rate thresholds; saturation signals (issue #11)
- `specs/observability/09-logging-schema.md` — 11 mandatory JSON fields with PII masking rules; log levels; event vocabulary; Loki label set; retention per environment (issue #11)
- `specs/observability/10-tracing-schema.md` — span naming convention; 11 mandatory attributes; sampling strategy; W3C TraceContext with incident_id extension; end-to-end agent hop example (issue #11)
- `specs/observability/11-slo-definitions.md` — 5 SLIs; SLO targets per tier; multi-window burn-rate thresholds; error budget policy; on-call trigger conditions (issue #11)
- `specs/sdlc/04-definition-of-done.md` — DoD checklists per story type (feat/fix/security/docs/refactor/chore) + Release DoD (issue #10)
- `specs/sdlc/05-branching-strategy.md` — Trunk-based branch patterns, naming convention, protection rules, hotfix flow (issue #10)
- `specs/sdlc/06-pr-and-review-process.md` — PR checklist, all 14 CI gates + 4 doc gates, reviewer obligations, merge ceremony (issue #10)
- `specs/sdlc/07-release-process.md` — SemVer policy, CHANGELOG automation, blue-green flow, rollback triggers and RTO targets (issue #10)
- `specs/system/00-project-brief.md` — Vision, objectives, scope and success criteria; RQ1–RQ4 traceability (issue #9)
- `specs/system/01-system-architecture.md` — C4 Level 1 + Level 2 diagrams; hexagonal layer constraints; PII boundary data flow (issue #9)
- `specs/system/02-agent-design.md` — 6-agent roster; orchestrator state machine; HITL/HOTL trigger matrix; AgentMessage schema (issue #9)
- `specs/system/03-incident-lifecycle.md` — Full lifecycle stages; MTTD/MTTR formal definitions; quantitative targets per severity (issue #9)
- `docs/adr/ADR-0027-privacy-by-design-sdlc.md` — Privacy by Design at all 7 SDLC phases; mandatory Privacy Impact section in every spec (issue #8)
- `docs/adr/ADR-0028-pii-sanitization-llm-apis.md` — Presidio + regex PII sanitization gate before every LLM API call; `sanitized=True` hard gate (issue #8)
- `docs/adr/ADR-0029-dpia-ripd-before-production.md` — DPIA/RIPD hard production gate; 6-section document with DPO sign-off required (issue #8)
- `docs/adr/ADR-0030-data-retention-ttl-policy.md` — Explicit TTL per data category; LLM prompts never persisted; automated deletion (issue #8)
- `docs/adr/ADR-0031-anonymization-standard-agent-datasets.md` — k-anonymity (k≥5) + differential privacy (ε=1.0) + utility ≥80% for research corpora (issue #8)
- `docs/adr/ADR-0032-cross-border-data-transfer-safeguards.md` — Transfer register for Anthropic, GitHub, cloud providers; SCCs + LGPD art. 33 VI research basis (issue #8)
- `prompt.md` — Full session transcript with timestamps for all prompts and responses (issue #8)
- `docs/adr/ADR-0023-hitl-autonomous-remediation.md` — HITL cryptographic enforcement for all production remediation (issue #7)
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md` — Append-only hash-chained audit trail for every agent decision (issue #7)
- `docs/adr/ADR-0025-kill-switch-credential-revocation.md` — Kill-switch + credential revocation protocol with RTO < 60s (issue #7)
- `docs/adr/ADR-0026-algorithmic-bias-audit-cadence.md` — Quarterly bias audit for TriageAgent and RCAAgent with release gate (issue #7)

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
