# CLAUDE.md — Agentic AI as a Copilot to Reduce MTTD and MTTR During Incident Response

> **Instructions for Claude Code**: This file is the behavioral contract of the project.
> Read it in full before executing any task. It defines the specs, harness, skills, rules
> and ADRs that govern ALL technical decisions in this repository. Language rule: English only.

---

## 1. Project Vision

### 1.1 Purpose

This project designs, builds and validates an **Agentic AI Copilot** for Incident Response —
an autonomous system capable of perceiving, reasoning, acting and learning within complex
operational environments. The Copilot supports technology teams (SRE, Engineering, Support,
NOC) by reducing two critical operational metrics:

- **MTTD** — Mean Time to Detect: time between incident onset and detection
- **MTTR** — Mean Time to Recovery: time between detection and full resolution

The system acts as a cognitive copilot: it augments human capacity without replacing it,
operating under explicit autonomy boundaries (HITL/HOTL) with verifiable, auditable and
reversible actions at every stage of the incident lifecycle.

### 1.2 Core Problem

Modern distributed systems and microservice architectures generate observability data
(logs, metrics, traces) at a volume and velocity that exceeds human cognitive capacity
for timely detection and response. Existing AIOps solutions correlate and triage alerts
but fall short when the situation demands planning, acting and learning continuously in
dynamic environments. The gap is not in understanding incidents — it is in acting on them
safely, with governance and accountability built in from the start.

### 1.3 System Boundaries

| Dimension          | Scope                                                                              |
| ------------------ | ---------------------------------------------------------------------------------- |
| **Users**          | SRE, On-call Engineers, NOC, Support, Engineering leads                            |
| **Incident types** | Availability, latency, error rate and saturation incidents in cloud-native systems |
| **Autonomy model** | HITL for production remediation; HOTL for detection and triage                     |
| **Data sources**   | Logs, metrics (Golden Signals), distributed traces, runbooks, post-mortems         |
| **Out of scope**   | Security incident response (SIEM/SOC domain), hardware failures                    |

### 1.4 Architecture Pillars

| Pillar            | What it governs                                                 | Key skills       |
| ----------------- | --------------------------------------------------------------- | ---------------- |
| **SDLC**          | End-to-end development lifecycle, PR/review, release            | `sdlc/`          |
| **Observability** | Golden Signals, structured logs, distributed traces, dashboards | `observability/` |
| **DevSecOps**     | SAST, DAST, OWASP LLM Top 10, SBOM, supply chain                | `devsecops/`     |
| **Ethics**        | Autonomy limits, audit trail, bias auditing, value alignment    | `ethics/`        |
| **Privacy**       | PII masking, LGPD, GDPR, data retention, anonymization          | `privacy/`       |
| **Engineering**   | ADR governance, spec-driven development, harness                | `engineering/`   |
| **Writing**       | Technical documentation, release notes                          | `writing/`       |
| **Domain**        | Agentic AI taxonomy, incident lifecycle, MTTD/MTTR metrics      | `domain/`        |

### 1.5 Compliance Baseline

| Standard / Regulation          | Domain enforced                                     |
| ------------------------------ | --------------------------------------------------- |
| **EU AI Act** (Arts. 9, 12–14) | Human oversight, audit trail, transparency          |
| **NIST AI RMF**                | AI risk governance, autonomy controls               |
| **GDPR** (EU 2016/679)         | Data protection, DPIA, cross-border transfers       |
| **LGPD** (Lei 13.709/2018)     | Brazilian data protection, RIPD, ANPD notification  |
| **OWASP LLM Top 10**           | Security for LLM-based components                   |
| **SOC 2 Type II**              | Change management, audit logging, access control    |
| **ISO 27001**                  | Information security management                     |
| **SLSA Level 2**               | Supply chain integrity, SBOM, artifact provenance   |
| **PCI-DSS 6.3 / 11.3**         | SAST/DAST requirements for payment-adjacent systems |

### 1.6 Success Criteria

1. The Agentic Copilot demonstrably reduces MTTD and MTTR against a baseline (quantitative evidence required — no toy examples).
2. All 32 foundational ADRs are documented, reviewed and merged before production deployment.
3. All CI gates pass on every PR: zero Critical/High SAST findings, zero exposed secrets, zero Critical CVEs.
4. DPIA/RIPD completed and approved before any production release handling real incident data.
5. Observability pipelines enforce PII masking before ingestion into any third-party system.
6. HITL controls are active for all autonomous remediation actions in production.

---

## 2. Spec Driven Development (SDD)

Every artifact in this project — code, configuration, documentation, diagram,
infrastructure — must derive from an approved spec before implementation begins.
Never generate artifacts without a spec. If one does not exist, create it first
and wait for confirmation before proceeding (RULE-001).

> **Full spec hierarchy with per-file descriptions and ownership table:** `specs/README.md`

### 2.1 SDD Cycle

```
SPEC → REVIEW → APPROVE → IMPLEMENT → HARNESS → MERGE
```

| Step          | Rule                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------ |
| **SPEC**      | Written in Markdown with all five mandatory sections before any implementation                   |
| **REVIEW**    | At least one review from a domain expert (Tech Lead or Security Lead for security/privacy specs) |
| **APPROVE**   | Explicit approval recorded — no implicit or verbal approvals                                     |
| **IMPLEMENT** | All code, config and docs derived from the approved spec; no undocumented deviations             |
| **HARNESS**   | All applicable harness checks pass (section 3); blocking issues resolved, not bypassed           |
| **MERGE**     | Squash and merge into `main`; spec file updated if implementation revealed changes               |

Spec change rules:

- Changes to an existing spec require the PR to reference the spec file being modified.
- Changes that constitute an architectural decision require a new or updated ADR before the spec change is merged.
- Spec and ADR must be merged before the implementation PR that depends on them.

### 2.2 Spec Ownership and Review Cadence

| Spec domain      | Owner              | Mandatory reviewers         | Review cadence                                  |
| ---------------- | ------------------ | --------------------------- | ----------------------------------------------- |
| `system/`        | Tech Lead          | Engineering + Product       | Every major release                             |
| `sdlc/`          | Engineering Lead   | All engineers (DoD changes) | Quarterly or on process change                  |
| `observability/` | SRE Lead           | On-call rotation            | Quarterly or on SLO change                      |
| `security/`      | Security Lead      | Tech Lead + DevSecOps       | Every release + on CVE event                    |
| `ethics/`        | Tech Lead          | Ethics reviewer + Legal     | Semi-annually or on model change                |
| `privacy/`       | DPO / Privacy Lead | Legal + Security Lead       | Before every production deploy with PII changes |

---

## 3. Harness Engineering

The harness is the automated verification layer that enforces quality, security and
consistency gates at every stage of the SDLC. No artifact — code, configuration,
documentation or infrastructure — is considered done until the applicable harness
passes in full. All checks are defined in `harness/` and executed by CI pipelines
in `.github/workflows/`.

**Harness principle**: gates are binary. A check either passes or blocks. No warnings
promoted to errors later, no manual overrides without an ADR.

> **Full gate definitions with YAML configs:**
> `harness/code-check.yml` (PR gate) · `harness/staging-check.yml` (staging gate) ·
> `harness/release-check.yml` (release gate) · `harness/doc-check.yml` (doc gate)

### 3.1 Harness Execution Summary

| Harness       | Trigger                      | Blocks            | Config file                 |
| ------------- | ---------------------------- | ----------------- | --------------------------- |
| PR Gate       | Every pull request           | Merge             | `harness/code-check.yml`    |
| Staging Gate  | Post-deploy to staging       | Production deploy | `harness/staging-check.yml` |
| Release Gate  | Pre-deploy to production     | Release           | `harness/release-check.yml` |
| Documentation | Changes to docs/specs/skills | Merge             | `harness/doc-check.yml`     |

---

## 4. Skills

Skills are specialized capabilities that Claude Code activates contextually.
This project uses local skills (in `skills/`) and enterprise-grade shared skills.

> **Full project skills catalog with descriptions:** `skills/project-skills-catalog.md`
> **Enterprise shared skills (SRE, DevSecOps, Observability, etc.):** `skills/README.md`

### 4.1 Skill Activation

| Trigger (detected context)                                       | Skill to activate                                                 |
| ---------------------------------------------------------------- | ----------------------------------------------------------------- |
| **writing/**                                                     |                                                                   |
| Technical documentation for a component or service               | `writing/tech-docs.md`                                            |
| New release, version bump or changelog                           | `writing/release-notes.md`                                        |
| **sdlc/**                                                        |                                                                   |
| Requirements elicitation or refinement                           | `sdlc/requirements.md`                                            |
| System design or architecture review                             | `sdlc/design.md`                                                  |
| Coding standards, commit convention or branch strategy           | `sdlc/implementation.md`                                          |
| PR opening, author checklist or CI gates                         | `sdlc/pull-request.md`                                            |
| PR review, feedback resolution, approvals or merge strategy      | `sdlc/pull-request.md`                                            |
| Test strategy, coverage or pyramid layer                         | `sdlc/testing.md`                                                 |
| Deployment strategy, rollback or feature flag                    | `sdlc/deployment.md`                                              |
| Post-mortem, runbook, SLO/SLI definition or review               | `sdlc/operations.md`                                              |
| **observability/**                                               |                                                                   |
| Structured logging, log levels or log schema                     | `observability/logs.md`                                           |
| Metrics, alerting, Golden Signals or SLO thresholds              | `observability/metrics.md`                                        |
| Distributed tracing, OpenTelemetry, span design or RCA           | `observability/traces.md`                                         |
| NOC, engineering or CUJ dashboard design                         | `observability/dashboards.md`                                     |
| **devsecops/**                                                   |                                                                   |
| Threat modeling, security principles or secure coding            | `devsecops/secure-development.md`                                 |
| OWASP Web Top 10, OWASP LLM Top 10 or Prompt Injection           | `devsecops/owasp.md`                                              |
| Static analysis, Semgrep, CodeQL or SonarQube                    | `devsecops/sast.md`                                               |
| Dynamic analysis, OWASP ZAP, Burp Suite or pentest               | `devsecops/dast.md`                                               |
| SBOM, CVE scanning, dependency pinning or supply chain security  | `devsecops/supply-chain.md`                                       |
| **ethics/**                                                      |                                                                   |
| AI ethics, fairness, accountability, XAI or EU AI Act            | `ethics/ai-ethics.md`                                             |
| Agent autonomy, delegation limits or value alignment             | `ethics/agentic-ethics.md`                                        |
| Algorithmic bias, decision auditing or shadow agents             | `ethics/bias-fairness.md`                                         |
| **privacy/**                                                     |                                                                   |
| PII identification, classification or masking                    | `privacy/pii.md`                                                  |
| LGPD, ANPD, RIPD, DPO or sensitive data (Brazil)                 | `privacy/lgpd.md`                                                 |
| GDPR, DPIA, data subject rights or cross-border transfers        | `privacy/gdpr.md`                                                 |
| Privacy by Design, data retention, encryption or RBAC            | `privacy/data-protection.md`                                      |
| Anonymization, pseudonymization, k-anonymity, DP or tokenization | `privacy/anonymization.md`                                        |
| **engineering/**                                                 |                                                                   |
| Architectural or technical decision to document                  | `engineering/adr-template.md`                                     |
| New spec creation                                                | `engineering/spec-template.md`                                    |
| Harness configuration or check rules                             | `engineering/harness-config.md`                                   |
| **domain/**                                                      |                                                                   |
| Agent architecture, guardrails, HITL or HOTL                     | `domain/agentic-ai-taxonomy.md` + `domain/guardrails-patterns.md` |
| Incident lifecycle, RCA or remediation flow                      | `domain/incident-lifecycle.md`                                    |
| MTTD, MTTR or IR efficiency metrics                              | `domain/mttd-mttr-metrics.md`                                     |

### 4.2 Canonical Glossary

Always use these definitions. Never redefine without creating an ADR.

| Term              | Definition                                                                    |
| ----------------- | ----------------------------------------------------------------------------- |
| **MTTD**          | Mean Time to Detect — time between incident onset and detection               |
| **MTTR**          | Mean Time to Recovery — time between detection and full resolution            |
| **Agentic AI**    | AI system with autonomous cycle of perception, reasoning, action and learning |
| **Copilot (IR)**  | Collaborative AI that augments human capacity without replacing it            |
| **AIOps**         | Application of ML/AI for IT operations automation                             |
| **HITL**          | Human-in-the-Loop — human approves each agent action                          |
| **HOTL**          | Human-on-the-Loop — human monitors, agent acts with override available        |
| **CUJ**           | Critical User Journey — critical user path affected by the incident           |
| **Guardrail**     | Executable technical control that limits or validates agent actions           |
| **Observability** | Ability to infer internal state via logs, metrics and traces                  |
| **SRE**           | Site Reliability Engineering — software engineering applied to operations     |

---

## 5. Rules

### 5.1 General Rules

- **RULE-001**: Never generate an artifact without an approved spec. If none exists, create it first and await confirmation.
- **RULE-002**: Every factual claim about MTTD/MTTR or Agentic AI efficacy must cite a bibliographic source (ABNT).
- **RULE-003**: Always distinguish between real empirical evidence and toy examples/proof of concept. Never equate the two.
- **RULE-004**: When a paper has QA score < 1.5, it may only be used for theoretical context — never to support quantitative claims.
- **RULE-005**: All skills, specs, code, ADRs and technical artifacts are written in English. See language rule in section 4.
- **RULE-006**: Every architectural decision that affects the SLR, code or project structure must generate an ADR (see section 6).

### 5.2 Research Rules

- **RULE-R01**: The canonical search string is: `("Agentic AI" OR "Multi-Agent System*") AND ("Incident Response" OR "Incident Management" OR "Incident Resolution" OR "HITL" OR "HOTL")`. Any variation requires an ADR.
- **RULE-R02**: Coverage period: 2020–2026. Papers outside this period require explicit justification.
- **RULE-R03**: Minimum inclusion criteria: SJR Q1 or Q2, Qualis A1 or A2, ≥ 1 citation.
- **RULE-R04**: The PRISMA flow (Identification → Screening → Eligibility → Inclusion) must be followed and documented.
- **RULE-R05**: Automated remediation must be distinguished from remediation recommendation — they are different stages of the IR cycle.

### 5.3 Code Rules

- **RULE-C01**: Every analysis script must have a docstring explaining which RQ it supports.
- **RULE-C02**: Test fixtures must use real data from included papers (P1–P19+), not synthetic data.
- **RULE-C03**: No sensitive data (credentials, personal data) in the repository. Use environment variables.
- **RULE-C04**: Harness must pass (green) before any merge into `main`.

---

## 6. Architecture Decision Records (ADR)

Every significant decision that affects the project must be documented as an ADR in `docs/adr/`.

> **ADR template and foundational ADR index (ADR-0001 to ADR-0032):** `docs/adr/README.md`

### 6.1 When to Create an ADR

Create an ADR whenever you:

- Alter SLR inclusion/exclusion criteria
- Change the search string
- Add or remove a research database
- Alter quality rubrics (QA1–QA4)
- Make a system architectural decision (e.g. agent framework choice, LLM model)
- Change the dissertation chapter structure
- Adopt a new tool or library in the project

### 6.2 Naming Convention

```
docs/adr/ADR-NNNN-title-kebab-case.md
```

Examples:

```
docs/adr/ADR-0001-canonical-search-string.md
docs/adr/ADR-0002-slr-inclusion-exclusion-criteria.md
docs/adr/ADR-0003-multi-agent-framework-selection.md
docs/adr/ADR-0004-adding-springer-arxiv-databases.md
```

---

## 7. Repository Structure

> **Full annotated repository tree:** `docs/repo-structure.md`

| Directory / File         | Purpose                                                          |
| ------------------------ | ---------------------------------------------------------------- |
| `specs/`                 | SDD specs — 22 spec files across 5 domains (section 2)           |
| `docs/adr/`              | Architecture Decision Records — ADR-0001 to ADR-0032 (section 6) |
| `docs/repo-structure.md` | Full annotated directory tree                                    |
| `skills/`                | Project and enterprise skills (section 4)                        |
| `harness/`               | Harness check YAML configs (section 3)                           |
| `src/`                   | Application source — agents, tools, memory, guardrails, api      |
| `tests/`                 | Test suite — unit, integration, e2e, security, fixtures          |
| `infrastructure/`        | IaC — terraform, helm, monitoring                                |
| `.github/workflows/`     | CI/CD pipelines — ci, cd-staging, cd-production, sbom            |
| `CHANGELOG.md`           | Release notes (Keep a Changelog + SemVer)                        |
| `SECURITY.md`            | Vulnerability disclosure policy                                  |
| `PRIVACY.md`             | Data processing notice (LGPD / GDPR)                             |

---

## 8. Standard Workflow

For every task in this project, execute the steps in order. Do not skip steps.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK ENTRY POINT                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. READ                                                        │
│     Read this CLAUDE.md in full before any action.             │
│     If already loaded in context, confirm language rule (EN)   │
│     and locate the relevant section for the task.              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. IDENTIFY SPEC                                               │
│     → Does a spec exist in specs/ for this task?               │
│       YES → load it and use its acceptance criteria            │
│       NO  → create the spec first, await confirmation,         │
│             then proceed (RULE-001)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. ACTIVATE SKILLS                                             │
│     → Match task context to section 4.1 activation table       │
│     → Load all matching skills before writing any output       │
│     → If multiple skills match, load all — they compose        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. CHECK ADRs                                                  │
│     → Scan docs/adr/ for any ADR relevant to the task          │
│     → If an ADR governs this area, its decision is final       │
│     → Overriding an ADR requires a new ADR — not a workaround  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. APPLY RULES                                                 │
│     → Enforce all applicable rules from section 5:             │
│       · RULE-001–006  General rules                            │
│       · RULE-R01–R05  Research rules                           │
│       · RULE-C01–C04  Code rules                               │
│     → Conflicts between rules → escalate, do not resolve       │
│       silently                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. EXECUTE                                                     │
│     → Produce the artifact: code, doc, analysis, diagram       │
│     → Security checks inline during execution:                 │
│       · No PII in output without masking (privacy/pii.md)      │
│       · No secrets or credentials in any file                  │
│       · OWASP LLM checklist applied to agent-related code      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. RUN HARNESS                                                 │
│     → Code artifact    → harness/code-check.yml                │
│     → Documentation    → harness/doc-check.yml                 │
│     → Research data    → harness/research-check.yml            │
│     → PR opened        → all CI gates in .github/workflows/    │
│     → All checks GREEN before proceeding                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. OPEN PR (if code changed)                                   │
│     → Follow sdlc/pull-request.md checklist                    │
│     → Fill PR template (.github/pull_request_template.md)      │
│     → Link issue, ADR and spec in PR description               │
│     → Minimum approvals by PR type (see sdlc/pull-request.md)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  9. CREATE ADR (if a significant decision was made)             │
│     → Use template from docs/adr/README.md                     │
│     → File under docs/adr/ADR-NNNN-title-kebab-case.md         │
│     → Reference affected skills, rules and compliance drivers  │
│     → ADR must be merged before the artifact it governs        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  10. UPDATE CHANGELOG                                           │
│      → Add entry to CHANGELOG.md (writing/release-notes.md)    │
│      → Category: Added | Changed | Fixed | Security | Removed  │
│      → Reference issue, ADR or PR number in each entry         │
└─────────────────────────────────────────────────────────────────┘
```

---

_Last updated: 2026-05-17 | Version: 1.2.0 | Author: Valdomiro de Oliveira Souza Júnior — PPGCA/Unisinos_
