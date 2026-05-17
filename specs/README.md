# Spec Hierarchy — Agentic AI Incident Response Copilot

> Extracted from CLAUDE.md §2.1. Authoritative reference for all spec files in this directory.
> Every spec must contain: **Purpose**, **Context**, **Decision**, **Acceptance Criteria**, **Linked ADRs**.

```
specs/
│
├── system/                          ← What the system is
│   ├── 00-project-brief.md            · Vision, objectives, scope and success criteria
│   │                                    Owner: Tech Lead | Review: every major release
│   ├── 01-system-architecture.md      · C4 Context + Container; architectural constraints
│   │                                    Linked ADRs: ADR-0001, ADR-0002
│   ├── 02-agent-design.md             · Agent roles, orchestration pattern, autonomy levels
│   │                                    Linked ADRs: ADR-0003, ADR-0004
│   └── 03-incident-lifecycle.md       · Failure Perception → RCA → Remediation flow
│                                        MTTD/MTTR acceptance criteria per stage
│
├── sdlc/                            ← How the team builds
│   ├── 04-definition-of-done.md       · DoD checklist: code, tests, docs, security,
│   │                                    observability requirements per story type
│   ├── 05-branching-strategy.md       · Trunk-based rules, branch naming conventions,
│   │                                    protection policies
│   │                                    Linked ADRs: ADR-0005
│   ├── 06-pr-and-review-process.md    · PR template, CI gate definitions,
│   │                                    reviewer assignment and approval thresholds
│   │                                    Linked ADRs: ADR-0007
│   └── 07-release-process.md          · SemVer policy, release checklist,
│                                        CHANGELOG requirements, rollback procedure
│                                        Linked ADRs: ADR-0006, ADR-0009
│
├── observability/                   ← How the system is monitored
│   ├── 08-golden-signals.md           · Latency/Error/Traffic/Saturation definitions,
│   │                                    p50/p95/p99 targets per service
│   │                                    Linked ADRs: ADR-0011
│   ├── 09-logging-schema.md           · Mandatory JSON fields, log levels,
│   │                                    retention policy per environment
│   │                                    Linked ADRs: ADR-0013, ADR-0014
│   ├── 10-tracing-schema.md           · Span naming conventions, mandatory attributes,
│   │                                    sampling strategy per criticality level
│   │                                    Linked ADRs: ADR-0012
│   └── 11-slo-definitions.md          · SLO/SLI/SLA per service, error budget policy,
│                                        alert threshold rules and on-call triggers
│                                        Linked ADRs: ADR-0015
│
├── security/                        ← How the system is secured
│   ├── 12-threat-model.md             · STRIDE analysis per component,
│   │                                    attack surface map, mitigations inventory
│   │                                    Linked ADRs: ADR-0016
│   ├── 13-sast-dast-policy.md         · Tool selection, scan frequency, severity
│   │                                    thresholds, remediation SLAs per finding level
│   │                                    Linked ADRs: ADR-0017, ADR-0018
│   ├── 14-secrets-management.md       · Vault policy, rotation schedule,
│   │                                    audit rules, emergency revocation procedure
│   │                                    Linked ADRs: ADR-0020
│   └── 15-supply-chain-policy.md      · SBOM format, dependency pinning rules,
│                                        CVE triage SLA, license allowlist
│                                        Linked ADRs: ADR-0019, ADR-0022
│
├── ethics/                          ← How the agent behaves responsibly
│   ├── 16-autonomy-boundaries.md      · What agents can/cannot do without human approval,
│   │                                    HITL/HOTL trigger conditions per action type
│   │                                    Linked ADRs: ADR-0023, ADR-0025
│   ├── 17-audit-trail.md              · Immutable decision log schema, retention rules,
│   │                                    access control and tamper-evidence requirements
│   │                                    Linked ADRs: ADR-0024
│   └── 18-bias-audit-plan.md          · Quarterly review cadence, bias metrics,
│                                        responsible party, remediation criteria
│                                        Linked ADRs: ADR-0026
│
└── privacy/                         ← How personal data is protected
    ├── 19-pii-inventory.md             · Data Flow Diagram, PII categories per service,
    │                                    masking rules for logs, traces and LLM prompts
    │                                    Linked ADRs: ADR-0027, ADR-0028
    ├── 20-data-retention-policy.md     · TTL per data category, deletion procedure,
    │                                    audit evidence requirements
    │                                    Linked ADRs: ADR-0030
    ├── 21-dpia-ripd.md                 · Impact assessment for Agentic AI features,
    │                                    risk register, safeguards and review cadence
    │                                    Linked ADRs: ADR-0029
    └── 22-anonymization-standard.md    · Technique selection per use case,
                                         validation procedure, re-identification risk test
                                         Linked ADRs: ADR-0031, ADR-0032
```

## Spec Ownership and Review Cadence

| Spec domain      | Owner              | Mandatory reviewers         | Review cadence                                  |
| ---------------- | ------------------ | --------------------------- | ----------------------------------------------- |
| `system/`        | Tech Lead          | Engineering + Product       | Every major release                             |
| `sdlc/`          | Engineering Lead   | All engineers (DoD changes) | Quarterly or on process change                  |
| `observability/` | SRE Lead           | On-call rotation            | Quarterly or on SLO change                      |
| `security/`      | Security Lead      | Tech Lead + DevSecOps       | Every release + on CVE event                    |
| `ethics/`        | Tech Lead          | Ethics reviewer + Legal     | Semi-annually or on model change                |
| `privacy/`       | DPO / Privacy Lead | Legal + Security Lead       | Before every production deploy with PII changes |

---

_Source: CLAUDE.md §2 | SDD cycle and rules: see CLAUDE.md §2 and §5_
