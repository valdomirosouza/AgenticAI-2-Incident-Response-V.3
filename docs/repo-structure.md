# Repository Structure — Agentic AI Incident Response Copilot

> Extracted from CLAUDE.md §7. Annotated reference for the full project directory tree.

```
AgenticAI-2-Incident-Response/
├── CLAUDE.md                          ← Behavioral contract for Claude Code
│
├── specs/                             ← SDD specs (CLAUDE.md §2 | specs/README.md)
│   ├── system/                          ← System-level specs
│   │   ├── 00-project-brief.md            · Vision, objectives, scope and success criteria
│   │   ├── 01-system-architecture.md      · C4 Context + Container; links to ADR-0001, ADR-0002
│   │   ├── 02-agent-design.md             · Agent roles, orchestration pattern and autonomy
│   │   │                                    levels (links to ADR-0003, ADR-0004)
│   │   └── 03-incident-lifecycle.md       · Failure Perception → RCA → Remediation flow
│   │                                        with MTTD/MTTR acceptance criteria per stage
│   │
│   ├── sdlc/                            ← SDLC process specs
│   │   ├── 04-definition-of-done.md       · DoD checklist: code, tests, docs, security gates
│   │   ├── 05-branching-strategy.md       · Trunk-based rules, branch naming (ADR-0005)
│   │   ├── 06-pr-and-review-process.md    · PR template, CI gate definitions (ADR-0007)
│   │   └── 07-release-process.md          · SemVer policy, CHANGELOG requirements (ADR-0006)
│   │
│   ├── observability/                   ← Observability specs
│   │   ├── 08-golden-signals.md           · Latency/Error/Traffic/Saturation (ADR-0011)
│   │   ├── 09-logging-schema.md           · Mandatory JSON fields, retention (ADR-0013)
│   │   ├── 10-tracing-schema.md           · Span naming, sampling strategy (ADR-0012)
│   │   └── 11-slo-definitions.md          · SLO/SLI/SLA, error budget policy (ADR-0015)
│   │
│   ├── security/                        ← Security specs
│   │   ├── 12-threat-model.md             · STRIDE analysis, attack surface (ADR-0016)
│   │   ├── 13-sast-dast-policy.md         · Tool selection, severity thresholds (ADR-0017, 0018)
│   │   ├── 14-secrets-management.md       · Vault policy, rotation schedule (ADR-0020)
│   │   └── 15-supply-chain-policy.md      · SBOM format, CVE triage SLA (ADR-0019, 0022)
│   │
│   ├── ethics/                          ← Ethics and AI governance specs
│   │   ├── 16-autonomy-boundaries.md      · HITL/HOTL triggers per action type (ADR-0023)
│   │   ├── 17-audit-trail.md              · Immutable decision log schema (ADR-0024)
│   │   └── 18-bias-audit-plan.md          · Quarterly review cadence (ADR-0026)
│   │
│   └── privacy/                         ← Privacy and data protection specs
│       ├── 19-pii-inventory.md             · Data Flow Diagram, masking rules (ADR-0028)
│       ├── 20-data-retention-policy.md     · TTL per data category (ADR-0030)
│       ├── 21-dpia-ripd.md                 · Impact assessment, risk register (ADR-0029)
│       └── 22-anonymization-standard.md    · Technique selection, re-id risk test (ADR-0031)
│
├── docs/                              ← Project documentation
│   ├── adr/                             ← Architecture Decision Records (docs/adr/README.md)
│   │   ├── ADR-0001-c4-model-architecture-documentation.md
│   │   ├── ADR-0002-hexagonal-architecture-agent-services.md
│   │   ├── ADR-0003-llm-provider-model-selection.md
│   │   ├── ADR-0004-multi-agent-orchestration-pattern.md
│   │   ├── ADR-0005-trunk-based-development-branching.md
│   │   ├── ADR-0006-conventional-commits-semver.md
│   │   ├── ADR-0007-pr-merge-gates-ci-checks.md
│   │   ├── ADR-0008-test-coverage-thresholds.md
│   │   ├── ADR-0009-blue-green-deployment-strategy.md
│   │   ├── ADR-0010-blameless-post-mortem-format.md
│   │   ├── ADR-0011-golden-signals-canonical-metric-set.md
│   │   ├── ADR-0012-opentelemetry-instrumentation-standard.md
│   │   ├── ADR-0013-structured-json-logging-schema.md
│   │   ├── ADR-0014-pii-masking-observability-pipelines.md
│   │   ├── ADR-0015-slo-based-alerting-thresholds.md
│   │   ├── ADR-0016-stride-threat-modeling-method.md
│   │   ├── ADR-0017-sast-mandatory-pr-gate.md
│   │   ├── ADR-0018-dast-staging-before-release.md
│   │   ├── ADR-0019-cyclonedx-sbom-per-build.md
│   │   ├── ADR-0020-zero-trust-secrets-management.md
│   │   ├── ADR-0021-owasp-llm-top10-checklist.md
│   │   ├── ADR-0022-dependency-pinning-cve-scanning.md
│   │   ├── ADR-0023-hitl-autonomous-remediation.md
│   │   ├── ADR-0024-immutable-agent-audit-trail.md
│   │   ├── ADR-0025-kill-switch-credential-revocation.md
│   │   ├── ADR-0026-algorithmic-bias-audit-cadence.md
│   │   ├── ADR-0027-privacy-by-design-sdlc.md
│   │   ├── ADR-0028-pii-sanitization-llm-apis.md
│   │   ├── ADR-0029-dpia-ripd-before-production.md
│   │   ├── ADR-0030-data-retention-ttl-policy.md
│   │   ├── ADR-0031-anonymization-standard-agent-datasets.md
│   │   └── ADR-0032-cross-border-data-transfer-safeguards.md
│   │
│   ├── glossary.md                      · Canonical glossary (CLAUDE.md §4.2)
│   └── repo-structure.md                · This file
│
├── skills/                            ← Project and enterprise skills (CLAUDE.md §4)
│   ├── README.md                        · Enterprise-grade shared skills index
│   ├── project-skills-catalog.md        · Project-specific planned skills catalog
│   ├── writing/
│   ├── sdlc/
│   ├── observability/
│   ├── devsecops/
│   ├── ethics/
│   ├── privacy/
│   ├── engineering/
│   └── domain/
│
├── harness/                           ← Harness check configurations (CLAUDE.md §3)
│   ├── code-check.yml                   · PR gate: build, lint, tests, SAST, secrets, PII
│   ├── staging-check.yml                · Staging gate: smoke, DAST, observability, security
│   ├── release-check.yml                · Release gate: SBOM, compliance, performance, rollback
│   └── doc-check.yml                    · Doc gate: ADR format, spec format, traceability
│
├── src/                               ← Application source code
│   ├── agents/                          · Agent implementations (orchestrator, specialists)
│   ├── tools/                           · Agent tools: log reader, metric fetcher, RCA engine
│   ├── memory/                          · Agent memory layer (short-term, long-term, RAG)
│   ├── guardrails/                      · HITL/HOTL controls, kill-switch, rollback logic
│   ├── observability/                   · Instrumentation: OTel setup, metrics, structured logs
│   └── api/                             · Service API layer (endpoints, auth, rate limiting)
│
├── tests/                             ← Test suite
│   ├── unit/                            · Unit tests per module (target: ≥ 80% coverage)
│   ├── integration/                     · Integration tests (target: ≥ 60% coverage)
│   ├── e2e/                             · End-to-end scenario tests (incident lifecycle)
│   ├── security/                        · SAST configs, DAST scan definitions
│   └── fixtures/                        · Real corpus data fixtures (no synthetic mocks)
│
├── infrastructure/                    ← Infrastructure as Code
│   ├── terraform/                       · Cloud resources (compute, networking, storage)
│   ├── helm/                            · Kubernetes manifests and Helm charts
│   └── monitoring/                      · Dashboard definitions, alert rules, SLO configs
│
├── .github/                           ← CI/CD pipeline definitions
│   ├── workflows/
│   │   ├── ci.yml                       · PR gate: build, test, SAST, secrets scan, license
│   │   ├── cd-staging.yml               · Deploy to staging + DAST execution
│   │   ├── cd-production.yml            · Blue-green deploy to production + smoke tests
│   │   └── sbom.yml                     · CycloneDX SBOM generation per release
│   └── pull_request_template.md         · PR template (linked to sdlc/pull-request.md)
│
├── CHANGELOG.md                       ← Release notes (Keep a Changelog + SemVer)
├── SECURITY.md                        ← Vulnerability disclosure policy
└── PRIVACY.md                         ← Data processing notice (LGPD / GDPR)
```

---

_Source: CLAUDE.md §7 | Last updated: 2026-05-17_
