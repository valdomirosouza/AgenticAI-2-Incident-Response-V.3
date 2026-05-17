# Architecture Decision Records — Agentic AI Incident Response Copilot

> Extracted from CLAUDE.md §6.3 and §6.4.
> ADR naming convention: `docs/adr/ADR-NNNN-title-kebab-case.md`
> Rules for when to create an ADR: see CLAUDE.md §6.

---

## ADR Template

```markdown
# ADR-NNNN: [Decision Title]

**Status**: [Proposed | Accepted | Superseded by ADR-XXXX | Deprecated]
**Date**: YYYY-MM-DD
**Deciders**: [names or roles]
**Affected RQs**: [RQ1, RQ2, ...]

---

## Context

[Describe the situation that made this decision necessary.
What problem was being solved? What pressure or constraint existed?]

## Decision

[Describe the decision taken in affirmative and clear terms.
E.g.: "We adopted X because Y."]

## Alternatives Considered

| Alternative | Pros | Cons |
| ----------- | ---- | ---- |
| Option A    |      |      |
| Option B    |      |      |

## Consequences

**Positive:**

- [list]

**Negative / Trade-offs:**

- [list]

## Review Criteria

[When should this decision be revisited? What evidence would change the decision?]

## References

- [links, papers, related specs]
```

---

## Foundational ADR Index

ADRs are grouped by domain. Each entry shows the decision, the skills it governs,
and the compliance driver that makes it non-negotiable.

---

### Architecture & Design

| ID       | Title                                                                                    | Skills governed                                                  | Compliance driver                             | Priority |
| -------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------- | -------- |
| ADR-0001 | Adoption of C4 Model as the standard for architecture documentation                      | `sdlc/design.md`, `writing/tech-docs.md`                         | ISO 27001 A.12.1 (documented ops)             | High     |
| ADR-0002 | Hexagonal Architecture as the structural pattern for agent services                      | `sdlc/design.md`, `domain/agentic-ai-taxonomy.md`                | SOC 2 CC6 (logical access boundaries)         | High     |
| ADR-0003 | Selection of LLM provider and model version for the Agentic Copilot                      | `domain/agentic-ai-taxonomy.md`, `devsecops/supply-chain.md`     | EU AI Act Art. 13 (transparency), OWASP LLM09 | High     |
| ADR-0004 | Multi-agent orchestration pattern: orchestrator + specialist agents vs. monolithic agent | `domain/agentic-ai-taxonomy.md`, `domain/guardrails-patterns.md` | NIST AI RMF GOVERN-1                          | High     |

---

### SDLC & Engineering

| ID       | Title                                                                | Skills governed                                         | Compliance driver                          | Priority |
| -------- | -------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------ | -------- |
| ADR-0005 | Trunk-based development as the branching strategy                    | `sdlc/implementation.md`, `sdlc/pull-request.md`        | DORA metrics (deployment frequency)        | High     |
| ADR-0006 | Conventional Commits + SemVer as the commit and versioning standard  | `sdlc/implementation.md`, `writing/release-notes.md`    | Auditability, SLSA Level 2                 | High     |
| ADR-0007 | Definition of PR merge gates: mandatory CI checks before merge       | `sdlc/pull-request.md`, `engineering/harness-config.md` | SOC 2 CC8.1 (change management)            | High     |
| ADR-0008 | Minimum test coverage thresholds: 80% unit, 60% integration          | `sdlc/testing.md`, `sdlc/pull-request.md`               | ISO 25010 (software quality)               | High     |
| ADR-0009 | Blue-Green deployment as default release strategy for production     | `sdlc/deployment.md`, `sdlc/operations.md`              | SRE SLO protection, ITIL Change Management | Medium   |
| ADR-0010 | Blameless post-mortem as the mandatory incident retrospective format | `sdlc/operations.md`, `domain/incident-lifecycle.md`    | ITIL 4 Problem Management                  | Medium   |

---

### Observability

| ID       | Title                                                                              | Skills governed                                                      | Compliance driver                        | Priority |
| -------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ---------------------------------------- | -------- |
| ADR-0011 | Golden Signals (Latency, Error, Traffic, Saturation) as the canonical metric set   | `observability/metrics.md`, `observability/dashboards.md`            | Google SRE Book, ISO 20000-1             | High     |
| ADR-0012 | OpenTelemetry as the unified instrumentation standard (traces, metrics, logs)      | `observability/traces.md`, `observability/logs.md`                   | W3C TraceContext, CNCF                   | High     |
| ADR-0013 | Structured JSON logging with mandatory fields: timestamp, service, trace_id, level | `observability/logs.md`, `privacy/pii.md`                            | ISO 27001 A.12.4 (logging), LGPD art. 48 | High     |
| ADR-0014 | PII masking in all logs and traces before ingestion into observability pipelines   | `observability/logs.md`, `observability/traces.md`, `privacy/pii.md` | LGPD art. 46, GDPR art. 5(1)(f)          | High     |
| ADR-0015 | SLO-based alerting thresholds (no fixed-value alerts)                              | `observability/metrics.md`, `sdlc/operations.md`                     | SRE error budget model                   | Medium   |

---

### DevSecOps & Security

| ID       | Title                                                                        | Skills governed                                           | Compliance driver                   | Priority |
| -------- | ---------------------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------- | -------- |
| ADR-0016 | STRIDE as the mandatory threat modeling method during design phase           | `devsecops/secure-development.md`, `sdlc/design.md`       | NIST SP 800-154, ISO 27005          | High     |
| ADR-0017 | SAST as a mandatory PR gate: zero Critical or High findings to merge         | `devsecops/sast.md`, `sdlc/pull-request.md`               | OWASP SAMM, PCI-DSS 6.3.2           | High     |
| ADR-0018 | DAST execution required in staging before every production release           | `devsecops/dast.md`, `sdlc/deployment.md`                 | PCI-DSS 11.3, OWASP ASVS            | High     |
| ADR-0019 | CycloneDX SBOM generated on every build and stored as release artifact       | `devsecops/supply-chain.md`, `writing/release-notes.md`   | SLSA Level 2, EO 14028 (US), EU CRA | High     |
| ADR-0020 | Zero-trust secrets management: no hardcoded credentials, vault mandatory     | `devsecops/secure-development.md`, `sdlc/pull-request.md` | CIS Controls v8 #14, SOC 2 CC6      | High     |
| ADR-0021 | OWASP LLM Top 10 applied as security checklist for all Agentic AI components | `devsecops/owasp.md`, `domain/agentic-ai-taxonomy.md`     | EU AI Act Art. 9, NIST AI RMF MAP-5 | High     |
| ADR-0022 | Dependency pinning with hash verification and automated CVE scanning         | `devsecops/supply-chain.md`, `sdlc/pull-request.md`       | SLSA Level 2, ISO 27001 A.14.2      | Medium   |

---

### Ethics & AI Governance

| ID       | Title                                                                                | Skills governed                                             | Compliance driver                                         | Priority |
| -------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------- | --------------------------------------------------------- | -------- |
| ADR-0023 | HITL required for all autonomous remediation actions in production                   | `domain/guardrails-patterns.md`, `ethics/agentic-ethics.md` | EU AI Act Art. 14 (human oversight), NIST AI RMF GOVERN-5 | High     |
| ADR-0024 | Immutable audit trail for every agent decision and action executed                   | `ethics/ai-ethics.md`, `engineering/adr-template.md`        | SOC 2 CC7, ISO 27001 A.12.4, EU AI Act Art. 12            | High     |
| ADR-0025 | Kill-switch and credential revocation protocol for compromised agents                | `domain/guardrails-patterns.md`, `ethics/agentic-ethics.md` | NIST AI RMF MANAGE-4, ISO 27001 A.16                      | High     |
| ADR-0026 | Algorithmic bias audit cadence: quarterly review of agent decisions by service group | `ethics/bias-fairness.md`, `sdlc/operations.md`             | EU AI Act Art. 10, IEEE 7000                              | Medium   |

---

### Privacy & Data Protection

| ID       | Title                                                                     | Skills governed                                                         | Compliance driver                            | Priority |
| -------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------- | -------- |
| ADR-0027 | Privacy by Design as a mandatory principle across all SDLC phases         | `privacy/data-protection.md`, `sdlc/design.md`                          | LGPD art. 46, GDPR art. 25                   | High     |
| ADR-0028 | PII sanitization before sending any data to external LLM APIs             | `privacy/pii.md`, `domain/agentic-ai-taxonomy.md`                       | LGPD art. 7, GDPR art. 6, OWASP LLM06        | High     |
| ADR-0029 | DPIA/RIPD required before production deployment of Agentic AI features    | `privacy/gdpr.md`, `privacy/lgpd.md`, `ethics/agentic-ethics.md`        | GDPR art. 35, LGPD art. 38, EU AI Act Art. 9 | High     |
| ADR-0030 | Data retention policy with explicit TTL per data category                 | `privacy/data-protection.md`, `observability/logs.md`                   | LGPD art. 16, GDPR art. 5(1)(e)              | High     |
| ADR-0031 | Anonymization standard for datasets used in agent training and evaluation | `privacy/anonymization.md`, `ethics/bias-fairness.md`                   | LGPD art. 12, GDPR Recital 26                | Medium   |
| ADR-0032 | Cross-border data transfer safeguards for observability and LLM providers | `privacy/gdpr.md`, `privacy/lgpd.md`, `devsecops/secure-development.md` | GDPR art. 46 (SCCs), LGPD art. 33            | Medium   |

---

### Phase 7 — Log-Ingestion-and-Metrics (LIM)

| ID       | Title                                                                 | Skills governed                                           | Compliance driver                           | Priority |
| -------- | --------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------- | -------- |
| ADR-0033 | LIM service location and project layout within the repository         | `sdlc/design.md`, `engineering/harness-config.md`         | ADR-0002 (hexagonal architecture extension) | High     |
| ADR-0034 | Redis Sorted Sets for latency distribution storage per window bucket  | `observability/metrics.md`, `devsecops/supply-chain.md`   | ADR-0030 (TTL policy), NIST AI RMF GOVERN-1 | High     |
| ADR-0035 | Exact ZRANK percentile algorithm via ZRANGE (no probabilistic sketch) | `observability/metrics.md`, `domain/mttd-mttr-metrics.md` | EU AI Act Art. 12 (auditability), ADR-0034  | High     |

---

_Source: CLAUDE.md §6.3 and §6.4 | ADR governance rules: CLAUDE.md §6_
