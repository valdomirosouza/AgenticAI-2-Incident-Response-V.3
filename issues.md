# Issues Index — Agentic AI Incident Response Copilot

> Implementation backlog organized by phase and dependency order.
> Every issue maps to one PR of work; every PR must pass all applicable harness gates before merge.
> GitHub board: https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues
> **Execution rule:** complete each phase before starting the next. Within a phase, issues in the same domain can run in parallel.

---

## Dependency Graph

```
Phase 0 — Bootstrap
    └── Phase 1 — ADRs (6 batches, sequential by domain dependency)
            └── Phase 2 — Specs (each domain unlocks after its ADRs are Accepted)
                    └── Phase 3 — Skills (each domain unlocks after its specs are merged)
                            └── Phase 4 — Harness & CI/CD
                                    └── Phase 5 — Source Code Scaffolding
```

---

## Phase 0 — Repository Bootstrap

| #                                                                                  | Issue                                                                                 | Deliverables                                                                                        | Priority |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | -------- |
| [#2](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/2) | Repository housekeeping: branch protection, PR template, CHANGELOG, SECURITY, PRIVACY | `.github/pull_request_template.md`, `CHANGELOG.md`, `SECURITY.md`, `PRIVACY.md`, `docs/glossary.md` | High     |

**Prerequisites:** none — start here.

---

## Phase 1 — ADRs: Architectural Foundation

All 32 foundational ADRs, batched by domain. Each batch must be merged and Accepted before the corresponding Phase 2 spec domain begins. Template: `docs/adr/README.md`.

| #                                                                                  | Issue                                           | ADRs                                                                                                                             | Compliance drivers                                | Priority |
| ---------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | -------- |
| [#3](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/3) | Architecture & Design: ADR-0001 to ADR-0004     | C4 Model, Hexagonal Architecture, LLM provider selection, multi-agent orchestration                                              | ISO 27001, SOC 2 CC6, EU AI Act Art. 13           | High     |
| [#4](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/4) | SDLC & Engineering: ADR-0005 to ADR-0010        | Trunk-based dev, Conventional Commits, PR gates, test coverage, Blue-Green deploy, blameless post-mortem                         | DORA, SLSA Level 2, SOC 2 CC8.1, ISO 25010        | High     |
| [#5](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/5) | Observability: ADR-0011 to ADR-0015             | Golden Signals, OpenTelemetry, JSON logging schema, PII masking, SLO-based alerting                                              | ISO 27001 A.12.4, LGPD art. 48, GDPR art. 5(1)(f) | High     |
| [#6](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/6) | DevSecOps & Security: ADR-0016 to ADR-0022      | STRIDE, SAST gate, DAST in staging, CycloneDX SBOM, vault secrets, OWASP LLM Top 10, dep pinning                                 | PCI-DSS 6.3/11.3, SLSA Level 2, EU AI Act Art. 9  | High     |
| [#7](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/7) | Ethics & AI Governance: ADR-0023 to ADR-0026    | HITL for autonomous remediation, immutable audit trail, kill-switch protocol, bias audit cadence                                 | EU AI Act Arts. 10/12/14, NIST AI RMF GOVERN-5    | High     |
| [#8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/8) | Privacy & Data Protection: ADR-0027 to ADR-0032 | Privacy by Design, PII sanitization for LLMs, DPIA/RIPD gate, data retention TTL, anonymization standard, cross-border transfers | LGPD arts. 7/33/38/46, GDPR arts. 6/25/35/46      | High     |

**Prerequisites:** Phase 0 (#2) complete.
**Reviewers required:** Security Lead (#6), Ethics reviewer + Legal (#7), DPO + Legal (#8).

---

## Phase 2 — Specs: System Contracts

22 spec files across 6 domains. Each spec must contain: **Purpose**, **Context**, **Decision**, **Acceptance Criteria**, **Linked ADRs**. Full hierarchy: `specs/README.md`.

| #                                                                                    | Issue                             | Specs                                                                                              | Prerequisite ADR batch | Priority |
| ------------------------------------------------------------------------------------ | --------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------- | -------- |
| [#9](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/9)   | System domain: specs 00–03        | `00-project-brief`, `01-system-architecture`, `02-agent-design`, `03-incident-lifecycle`           | #3 (ADR-0001–0004)     | High     |
| [#10](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/10) | SDLC domain: specs 04–07          | `04-definition-of-done`, `05-branching-strategy`, `06-pr-and-review-process`, `07-release-process` | #4 (ADR-0005–0010)     | High     |
| [#11](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/11) | Observability domain: specs 08–11 | `08-golden-signals`, `09-logging-schema`, `10-tracing-schema`, `11-slo-definitions`                | #5 (ADR-0011–0015)     | High     |
| [#12](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/12) | Security domain: specs 12–15      | `12-threat-model`, `13-sast-dast-policy`, `14-secrets-management`, `15-supply-chain-policy`        | #6 (ADR-0016–0022)     | High     |
| [#13](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/13) | Ethics domain: specs 16–18        | `16-autonomy-boundaries`, `17-audit-trail`, `18-bias-audit-plan`                                   | #7 (ADR-0023–0026)     | High     |
| [#14](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/14) | Privacy domain: specs 19–22       | `19-pii-inventory`, `20-data-retention-policy`, `21-dpia-ripd`, `22-anonymization-standard`        | #8 (ADR-0027–0032)     | High     |

**Prerequisites:** Corresponding ADR batch (Phase 1) merged and Accepted.
**Hard gate:** `21-dpia-ripd.md` must be approved before any production deploy with real incident data (CLAUDE.md §1.6 criterion 4).

---

## Phase 3 — Skills: Knowledge Library

~30 skill files across 7 domains. Each skill must follow the language rule: **English only** (CLAUDE.md §4). Activation triggers: `CLAUDE.md §4.1`.

| #                                                                                    | Issue                        | Skill files                                                                                               | Prerequisite specs                 | Priority |
| ------------------------------------------------------------------------------------ | ---------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------- | -------- |
| [#15](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/15) | Domain skills                | `agentic-ai-taxonomy`, `incident-lifecycle`, `mttd-mttr-metrics`, `guardrails-patterns`                   | #9 (system specs)                  | High     |
| [#16](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/16) | Writing & Engineering skills | `tech-docs`, `release-notes`, `adr-template`, `spec-template`, `harness-config`                           | #10 (SDLC specs)                   | High     |
| [#17](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/17) | SDLC skills                  | `requirements`, `design`, `implementation`, `pull-request`, `testing`, `deployment`, `operations`         | #10 (SDLC specs)                   | High     |
| [#18](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/18) | Observability skills         | `logs`, `metrics`, `traces`, `dashboards`                                                                 | #11 (observability specs)          | High     |
| [#19](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/19) | DevSecOps skills             | `secure-development`, `owasp`, `sast`, `dast`, `supply-chain`                                             | #12 (security specs)               | High     |
| [#20](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/20) | Ethics & Privacy skills      | `ai-ethics`, `agentic-ethics`, `bias-fairness`, `pii`, `lgpd`, `gdpr`, `data-protection`, `anonymization` | #13 + #14 (ethics + privacy specs) | Medium   |

**Prerequisites:** Corresponding spec domain (Phase 2) merged. Domain skills (#15) can start as soon as #9 merges.

---

## Phase 4 — Harness & CI/CD

Gates and pipelines that enforce every quality, security and consistency check automatically.

| #                                                                                    | Issue                       | Deliverables                                                                                                | Prerequisite specs/skills                                        | Priority |
| ------------------------------------------------------------------------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------- |
| [#21](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/21) | Harness configuration files | `harness/code-check.yml`, `harness/staging-check.yml`, `harness/release-check.yml`, `harness/doc-check.yml` | #10 (SDLC specs), #12 (security specs), #16 (engineering skills) | High     |
| [#22](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/22) | GitHub Actions workflows    | `.github/workflows/ci.yml`, `cd-staging.yml`, `cd-production.yml`, `sbom.yml`                               | #21 (harness files)                                              | High     |

**Prerequisites:** SDLC, Observability and Security specs (Phase 2) merged. Engineering skills (#16) available.

---

## Phase 5 — Source Code Scaffolding

Directory structure, module boundaries and entry-point stubs. Full implementation follows per-module in subsequent issues. Every file must be derived from an approved spec (CLAUDE.md §5 RULE-001).

| #                                                                                    | Issue                              | Deliverables                                                                                               | Prerequisite                                 | Priority |
| ------------------------------------------------------------------------------------ | ---------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------- | -------- |
| [#23](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/23) | Application source scaffolding     | `src/agents/`, `src/tools/`, `src/memory/`, `src/guardrails/`, `src/observability/`, `src/api/`            | All system + ethics specs, all ADRs accepted | High     |
| [#24](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/24) | Test suite scaffolding             | `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/security/`, `tests/fixtures/` (real corpus data) | #23 started, SDLC specs                      | High     |
| [#25](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/25) | Infrastructure as Code scaffolding | `infrastructure/terraform/`, `infrastructure/helm/`, `infrastructure/monitoring/`                          | Observability specs, system specs            | Medium   |

**Prerequisites:** Phase 4 complete. All 32 ADRs Accepted. All 22 specs approved.

---

## Summary

| Phase               | Issues                            | Artifacts                     | Status |
| ------------------- | --------------------------------- | ----------------------------- | ------ |
| 0 — Bootstrap       | #2                                | 5 files                       | Open   |
| 1 — ADRs            | #3 · #4 · #5 · #6 · #7 · #8       | 32 ADR files                  | Open   |
| 2 — Specs           | #9 · #10 · #11 · #12 · #13 · #14  | 22 spec files                 | Open   |
| 3 — Skills          | #15 · #16 · #17 · #18 · #19 · #20 | ~30 skill files               | Open   |
| 4 — Harness & CI/CD | #21 · #22                         | 4 harness YAMLs + 4 workflows | Open   |
| 5 — Src Scaffolding | #23 · #24 · #25                   | src/, tests/, infrastructure/ | Open   |
| **Total**           | **24 issues**                     | **~100 artifacts**            |        |

---

## Labels

| Label                               | Meaning                                       |
| ----------------------------------- | --------------------------------------------- |
| `phase:0-bootstrap` … `phase:5-src` | Execution phase                               |
| `type:adr`                          | Architecture Decision Record                  |
| `type:spec`                         | SDD spec artifact                             |
| `type:skill`                        | Skills library file                           |
| `type:harness`                      | Harness check configuration                   |
| `type:cicd`                         | CI/CD pipeline artifact                       |
| `type:src`                          | Source code artifact                          |
| `priority:high`                     | Blocks dependents — complete before moving on |
| `priority:medium`                   | Important but not blocking                    |

---

_Last updated: 2026-05-17 | Governed by: CLAUDE.md §8 Standard Workflow_
