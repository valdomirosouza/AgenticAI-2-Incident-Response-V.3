# Canonical Glossary — Agentic AI Incident Response Copilot

> Single source of truth for all project terminology.
> **Never redefine a term without creating an ADR** (CLAUDE.md §5 RULE-006).
> Terms used in code, specs, ADRs and skills must match the definitions below exactly.

---

## Core Terms

| Term              | Definition                                                                                                                                                                  |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MTTD**          | Mean Time to Detect — elapsed time between the onset of an incident and its detection by the system or team                                                                 |
| **MTTR**          | Mean Time to Recovery — elapsed time between incident detection and full service restoration                                                                                |
| **Agentic AI**    | An AI system with an autonomous cycle of perception, reasoning, action and learning; capable of pursuing goals across multiple steps without human involvement at each step |
| **Copilot (IR)**  | A collaborative AI system that augments human capacity during incident response without replacing human judgment or authority                                               |
| **AIOps**         | Application of machine learning and AI techniques to automate and enhance IT operations                                                                                     |
| **HITL**          | Human-in-the-Loop — an autonomy model where a human explicitly approves each agent action before execution                                                                  |
| **HOTL**          | Human-on-the-Loop — an autonomy model where the agent acts autonomously and a human monitors with the ability to override or halt                                           |
| **CUJ**           | Critical User Journey — the sequence of interactions a user follows to accomplish a key goal; used to define SLOs and assess incident impact on end users                   |
| **Guardrail**     | An executable technical control that constrains, validates or halts an agent action; enforced programmatically, not by policy alone                                         |
| **Observability** | The ability to infer the internal state of a system from its external outputs — logs, metrics and traces                                                                    |
| **SRE**           | Site Reliability Engineering — the discipline of applying software engineering principles to IT operations, with a focus on reliability, scalability and operability        |

## Incident Response Terms

| Term                   | Definition                                                                                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Incident**           | An unplanned interruption or degradation of a service that affects users or system reliability                                                                      |
| **Incident lifecycle** | The full sequence: Failure Perception → Detection → Triage → Root Cause Analysis → Remediation → Post-mortem                                                        |
| **RCA**                | Root Cause Analysis — systematic process of identifying the underlying cause(s) of an incident                                                                      |
| **Runbook**            | A documented, step-by-step procedure for responding to a known incident type or operational task                                                                    |
| **Post-mortem**        | A structured retrospective conducted after an incident to understand what happened, why, and how to prevent recurrence. Always blameless in this project (ADR-0010) |
| **Alert fatigue**      | Desensitization to alerts caused by excessive volume of low-quality or duplicate notifications, reducing team responsiveness                                        |
| **Triage**             | The process of assessing and prioritizing incidents by impact, urgency and likely cause                                                                             |

## Observability Terms

| Term                     | Definition                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| **Golden Signals**       | The four canonical metrics for service health defined in the Google SRE Book: Latency, Error Rate, Traffic and Saturation |
| **Latency**              | Time taken to service a request; tracked at p50, p95 and p99 percentiles — not just average                               |
| **Error Rate**           | Percentage of requests resulting in an error response (5xx or 4xx, as defined per service)                                |
| **Traffic**              | Volume of demand on a system, expressed as requests per second or events per second                                       |
| **Saturation**           | How close a resource is to its limit — CPU%, memory%, queue depth, thread pool usage                                      |
| **SLO**                  | Service Level Objective — an internal target for service reliability (e.g. 99.9% availability over 30 days)               |
| **SLI**                  | Service Level Indicator — the specific metric used to measure against an SLO                                              |
| **SLA**                  | Service Level Agreement — a contractual commitment to a customer, backed by SLOs                                          |
| **Error budget**         | The allowable amount of unreliability implied by an SLO; consumed by incidents and releases                               |
| **Distributed tracing**  | Tracking a request as it flows across multiple services, using a shared `trace_id` and per-service `span_id`              |
| **OpenTelemetry (OTel)** | The CNCF standard for instrumentation, collection and export of traces, metrics and logs                                  |

## Security & Privacy Terms

| Term                 | Definition                                                                                                                                         |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SAST**             | Static Application Security Testing — automated analysis of source code for vulnerabilities without executing the program                          |
| **DAST**             | Dynamic Application Security Testing — automated security testing of a running application                                                         |
| **SBOM**             | Software Bill of Materials — a formal inventory of all components, libraries and dependencies in a software artifact                               |
| **SLSA**             | Supply-chain Levels for Software Artifacts — a security framework for ensuring software supply chain integrity                                     |
| **PII**              | Personally Identifiable Information — any data that can identify a natural person, directly or indirectly                                          |
| **DPIA**             | Data Protection Impact Assessment (GDPR art. 35) — mandatory assessment for high-risk AI processing of personal data                               |
| **RIPD**             | Relatório de Impacto à Proteção de Dados — Brazilian equivalent of DPIA under LGPD art. 38                                                         |
| **Pseudonymization** | Processing personal data such that it can no longer be attributed to a specific data subject without additional information (still considered PII) |
| **Anonymization**    | Irreversible transformation of data such that individuals cannot be re-identified (no longer PII under LGPD/GDPR)                                  |
| **Zero trust**       | Security model that assumes no implicit trust for any entity, inside or outside the network perimeter                                              |

## Architecture & Engineering Terms

| Term                        | Definition                                                                                                                                           |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ADR**                     | Architecture Decision Record — a document capturing a significant architectural decision, its context, alternatives considered and consequences      |
| **SDD**                     | Spec-Driven Development — methodology where a formal spec is authored and approved before any implementation begins                                  |
| **Harness**                 | The automated verification layer that enforces quality, security and consistency gates at every SDLC stage                                           |
| **Hexagonal Architecture**  | Architectural pattern (Ports and Adapters) that isolates the domain from infrastructure; chosen for agent services in ADR-0002                       |
| **C4 Model**                | A hierarchical diagramming approach using four levels: Context, Container, Component, Code; chosen for architecture documentation in ADR-0001        |
| **Conventional Commits**    | A commit message specification that structures commits as `type(scope): description` for machine-readable changelogs and SemVer automation           |
| **Trunk-based development** | Branching strategy where all developers integrate to a single long-lived branch (`main`) frequently, using short-lived feature branches              |
| **Blue-Green deployment**   | Release strategy using two identical production environments; traffic is switched between them to enable zero-downtime releases and instant rollback |

## Compliance & Governance Terms

| Term                 | Definition                                                                                                                                                                    |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **EU AI Act**        | European Union regulation on artificial intelligence (2024), classifying AI systems by risk level and imposing requirements on transparency, human oversight and auditability |
| **NIST AI RMF**      | NIST AI Risk Management Framework — voluntary guidance for managing risks across the AI lifecycle                                                                             |
| **LGPD**             | Lei Geral de Proteção de Dados — Brazilian data protection law (Lei 13.709/2018), effective since 2020                                                                        |
| **GDPR**             | General Data Protection Regulation — EU data protection law (Regulation 2016/679)                                                                                             |
| **OWASP LLM Top 10** | OWASP's ranked list of the most critical security risks for applications using Large Language Models                                                                          |
| **SOC 2 Type II**    | Auditing standard for service organizations covering Security, Availability, Processing Integrity, Confidentiality and Privacy over a period of time                          |

---

_Source: CLAUDE.md §4.2 | Last updated: 2026-05-17 | To add a term or change a definition, create an ADR per RULE-006._
