# Agentic AI Copilot for Incident Response

> Reducing MTTD and MTTR through autonomous AI-orchestrated detection, triage and remediation.

**Master's Dissertation — PPGCA / Unisinos**
**Author:** Valdomiro de Oliveira Souza Júnior
**Version:** 1.2.0 (in progress) · **Last updated:** 2026-05-17

---

## Problem Statement

Modern distributed systems and microservice architectures generate observability data — logs, metrics, traces — at a volume and velocity that exceeds human cognitive capacity for timely incident response.

Existing AIOps solutions correlate and triage alerts, but fall short when the situation demands **planning, acting and learning continuously in dynamic environments**. The gap is not in _understanding_ incidents; it is in _acting on them safely_, with governance and accountability built in from the start.

**Consequences:**

- High MTTD — incidents go undetected for minutes or hours while alerts accumulate
- High MTTR — triage is manual, context is lost, runbooks are outdated, remediation is slow
- Alert fatigue reduces team responsiveness over time
- Distributed systems make root-cause correlation beyond manual reach at scale

---

## Solution

This project designs, builds and validates an **Agentic AI Copilot** for Incident Response — an autonomous system capable of perceiving, reasoning, acting and learning within complex operational environments.

```
Alert / Anomaly
      │
      ▼
┌─────────────────────────────────────────┐
│           Agentic AI Copilot            │
│                                         │
│  Perception → Reasoning → Action        │
│      (logs, metrics, traces)            │
│                                         │
│  Detection → Triage → RCA → Remediation │
└───────────┬──────────────┬──────────────┘
            │              │
     HOTL monitor    HITL approval
     (human on loop) (human in loop)
            │              │
            ▼              ▼
       Dashboard      Production
        + Alert        Remediation
```

The Copilot **augments** human capacity — it does not replace it. Every autonomous action in production requires explicit human approval (HITL). Detection and triage run autonomously under human oversight (HOTL) with override always available.

### Target Metrics

| Metric   | Definition                                      | Goal                                                |
| -------- | ----------------------------------------------- | --------------------------------------------------- |
| **MTTD** | Mean Time to Detect — onset to detection        | Reduce vs baseline (quantitative evidence required) |
| **MTTR** | Mean Time to Recovery — detection to resolution | Reduce vs baseline (quantitative evidence required) |

---

## Architecture

The system is governed by eight engineering domains:

| Pillar            | Scope                                                           |
| ----------------- | --------------------------------------------------------------- |
| **SDLC**          | End-to-end development lifecycle, PR/review, release            |
| **Observability** | Golden Signals, structured logs, distributed traces, dashboards |
| **DevSecOps**     | SAST, DAST, OWASP LLM Top 10, SBOM, supply chain                |
| **Ethics**        | Autonomy limits, audit trail, bias auditing, value alignment    |
| **Privacy**       | PII masking, LGPD, GDPR, data retention, anonymization          |
| **Engineering**   | ADR governance, spec-driven development, harness                |
| **Writing**       | Technical documentation, release notes                          |
| **Domain**        | Agentic AI taxonomy, incident lifecycle, MTTD/MTTR metrics      |

### Autonomy Model

| Layer                  | Mode                         | Description                                           |
| ---------------------- | ---------------------------- | ----------------------------------------------------- |
| Detection & Triage     | **HOTL** — Human on the Loop | Agent acts autonomously; human monitors with override |
| Production Remediation | **HITL** — Human in the Loop | Agent proposes; human approves before execution       |

### System Boundaries

| Dimension          | Scope                                                                      |
| ------------------ | -------------------------------------------------------------------------- |
| **Users**          | SRE, On-call Engineers, NOC, Support, Engineering leads                    |
| **Incident types** | Availability, latency, error rate, saturation — cloud-native systems       |
| **Data sources**   | Logs, metrics (Golden Signals), distributed traces, runbooks, post-mortems |
| **Out of scope**   | Security incident response (SIEM/SOC), hardware failures                   |

---

## Compliance Baseline

Non-negotiable requirements enforced through ADRs, specs and CI gates:

| Standard / Regulation          | Domain                                             |
| ------------------------------ | -------------------------------------------------- |
| **EU AI Act** (Arts. 9, 12–14) | Human oversight, audit trail, transparency         |
| **NIST AI RMF**                | AI risk governance, autonomy controls              |
| **GDPR** (EU 2016/679)         | Data protection, DPIA, cross-border transfers      |
| **LGPD** (Lei 13.709/2018)     | Brazilian data protection, RIPD, ANPD notification |
| **OWASP LLM Top 10**           | Security for LLM-based components                  |
| **SOC 2 Type II**              | Change management, audit logging, access control   |
| **ISO 27001**                  | Information security management                    |
| **SLSA Level 2**               | Supply chain integrity, SBOM, artifact provenance  |
| **PCI-DSS 6.3 / 11.3**         | SAST/DAST for payment-adjacent systems             |

---

## Success Criteria

This project is considered successful when:

1. The Copilot demonstrably reduces MTTD and MTTR against a baseline — quantitative evidence required, no toy examples.
2. All 32 foundational ADRs are documented, reviewed and merged before production deployment.
3. All CI gates pass on every PR: zero Critical/High SAST findings, zero exposed secrets, zero Critical CVEs.
4. DPIA/RIPD completed and approved before any production release handling real incident data.
5. Observability pipelines enforce PII masking before ingestion into any third-party system.
6. HITL controls are active for all autonomous remediation actions in production.

---

## Repository Structure

```
AgenticAI-2-Incident-Response-V.3/
│
├── CLAUDE.md                    ← Behavioral contract for Claude Code (v1.2.0)
├── issues.md                    ← Implementation backlog — 24 issues across 6 phases
├── CHANGELOG.md                 ← Release notes (Keep a Changelog + SemVer)
├── SECURITY.md                  ← Vulnerability disclosure policy
├── PRIVACY.md                   ← Data processing notice (LGPD / GDPR)
│
├── specs/                       ← 22 SDD specs across 6 domains
│   ├── README.md                  ← Spec hierarchy and ownership
│   ├── system/                    ← Vision, architecture, agent design, incident lifecycle
│   ├── sdlc/                      ← DoD, branching, PR process, release
│   ├── observability/             ← Golden Signals, logging, tracing, SLOs
│   ├── security/                  ← Threat model, SAST/DAST policy, secrets, supply chain
│   ├── ethics/                    ← Autonomy boundaries, audit trail, bias audit
│   └── privacy/                   ← PII inventory, data retention, DPIA/RIPD, anonymization
│
├── docs/
│   ├── adr/
│   │   └── README.md              ← ADR template + index of all 32 foundational ADRs
│   ├── glossary.md                ← Canonical glossary (MTTD, MTTR, HITL, HOTL, …)
│   └── repo-structure.md          ← Full annotated directory tree
│
├── skills/
│   ├── README.md                  ← Enterprise shared skills (SRE, DevSecOps, Observability…)
│   └── project-skills-catalog.md  ← Project-specific planned skills catalog
│
├── harness/                     ← Harness check YAML configs (Phase 4)
├── src/                         ← Application source code (Phase 5)
├── tests/                       ← Test suite (Phase 5)
├── infrastructure/              ← IaC — terraform, helm, monitoring (Phase 5)
└── .github/
    ├── workflows/               ← CI/CD pipelines (Phase 4)
    └── pull_request_template.md ← PR template (Phase 0)
```

---

## Implementation Roadmap

Full backlog with dependencies: [`issues.md`](./issues.md)
GitHub issues: [`github.com/…/issues`](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues)

| Phase                   | Milestone                                                              | Issues                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Status |
| ----------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| **0 — Bootstrap**       | Repo housekeeping, PR template, CHANGELOG, SECURITY, PRIVACY, glossary | [#2](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/2)                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Open   |
| **1 — ADRs**            | 32 foundational ADRs in 6 domain batches                               | [#3](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/3) · [#4](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/4) · [#5](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/5) · [#6](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/6) · [#7](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/7) · [#8](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/8)             | Open   |
| **2 — Specs**           | 22 SDD specs in 6 domains                                              | [#9](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/9) · [#10](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/10) · [#11](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/11) · [#12](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/12) · [#13](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/13) · [#14](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/14)   | Open   |
| **3 — Skills**          | ~30 project skill files in 7 domains                                   | [#15](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/15) · [#16](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/16) · [#17](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/17) · [#18](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/18) · [#19](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/19) · [#20](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/20) | Open   |
| **4 — Harness & CI/CD** | 4 harness YAMLs + 4 GitHub Actions workflows                           | [#21](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/21) · [#22](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/22)                                                                                                                                                                                                                                                                                                                                                             | Open   |
| **5 — Source Code**     | src/, tests/, infrastructure/ scaffolding                              | [#23](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/23) · [#24](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/24) · [#25](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/25)                                                                                                                                                                                                                                                                      | Open   |

---

## What Has Been Built (v1.2.0)

| Artifact                           | Description                                                                                                                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CLAUDE.md` v1.2.0                 | Behavioral contract for Claude Code: 8-pillar architecture, SDD cycle, harness rules, skill activation table, canonical glossary, 10-step workflow — split from 91 KB to 30 KB |
| `specs/README.md`                  | Spec hierarchy: 22 spec files across 6 domains with per-file descriptions and ownership table                                                                                  |
| `docs/adr/README.md`               | Canonical ADR template + index of all 32 foundational ADRs with compliance drivers                                                                                             |
| `docs/repo-structure.md`           | Full annotated directory tree                                                                                                                                                  |
| `skills/README.md`                 | 12 enterprise-grade shared skills: SRE, Observability, DevSecOps, Security by Design, AI Governance, SDD, SDLC Governance, Managing ADRs, Credentials, CI/CD, Documentation    |
| `skills/project-skills-catalog.md` | Catalog of 30+ planned project-specific skills across 8 domains                                                                                                                |
| `issues.md`                        | 24-issue implementation backlog organized in 6 phases with dependency graph                                                                                                    |
| GitHub Issues #2–#25               | 24 documented issues with acceptance criteria, deliverables and cross-references                                                                                               |
| GitHub Milestones                  | 6 milestones (one per phase)                                                                                                                                                   |
| GitHub Labels                      | 14 labels (`phase:`, `type:`, `priority:`)                                                                                                                                     |

---

## Development Methodology

This project follows **Spec-Driven Development (SDD)**:

```
SPEC → REVIEW → APPROVE → IMPLEMENT → HARNESS → MERGE
```

No artifact — code, configuration, documentation, diagram or infrastructure — is generated without an approved spec. Every architectural decision is documented as an ADR before the artifact it governs.

**Governing document:** [`CLAUDE.md`](./CLAUDE.md)

---

## License

Academic project — PPGCA / Unisinos. For research and dissertation purposes.
