# Spec 00: Project Brief

**Domain**: system
**Owner**: Tech Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #9
**Review cadence**: Every major release

---

## 1. Purpose

Define the vision, objectives, scope and success criteria of the Agentic AI Copilot for
Incident Response — the single authoritative reference that every spec, ADR and code
artifact derives from.

---

## 2. Context

Modern cloud-native platforms generate observability data (logs, metrics, traces) at a
volume and velocity that exceeds human cognitive capacity for timely detection and
response. Existing AIOps platforms correlate alerts but cannot plan, act and learn
continuously inside dynamic environments. The gap is not situational awareness — it is
safe, governed, accountable action.

This project is a doctoral research initiative (PPGCA/Unisinos) that designs, builds and
empirically evaluates an Agentic AI Copilot that:

1. Reduces **MTTD** (Mean Time to Detect) by autonomously correlating observability
   signals and detecting anomalies before human operators would.
2. Reduces **MTTR** (Mean Time to Recovery) by reasoning over root causes, proposing
   remediation steps, and executing approved actions within explicit autonomy boundaries.
3. Operates under **full governance**: every agent action is auditable, reversible and
   subject to human oversight as required by HITL/HOTL controls.

**Research questions this project answers:**

| RQ  | Question                                                                              |
| --- | ------------------------------------------------------------------------------------- |
| RQ1 | How does an Agentic AI architecture reduce MTTD in cloud-native incident response?    |
| RQ2 | How does the Copilot reduce MTTR against a human-only baseline?                       |
| RQ3 | What guardrails and autonomy controls are required for safe agentic IR in production? |
| RQ4 | How can the system be built in compliance with LGPD, GDPR and EU AI Act requirements? |

---

## 3. Decision

### 3.1 Vision statement

> An autonomous, auditable and privacy-preserving Agentic AI Copilot that measurably
> reduces MTTD and MTTR in cloud-native incident response, while keeping humans in
> control of every consequential action.

### 3.2 Objectives

| ID  | Objective                                                                          | Measurable outcome                                                |
| --- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| O1  | Detect incidents faster than human-only baselines                                  | MTTD reduced ≥ 20% versus baseline (quantitative, RQ1)            |
| O2  | Resolve incidents faster with Copilot assistance                                   | MTTR reduced ≥ 20% versus baseline (quantitative, RQ2)            |
| O3  | Operate within explicit autonomy limits at every stage of the incident lifecycle   | Zero unauthorized PRODUCTION\_\* executions in any test run (RQ3) |
| O4  | Achieve full compliance with LGPD, GDPR and EU AI Act before production deployment | DPIA/RIPD approved, all privacy ADRs merged (RQ4)                 |
| O5  | Produce replicable empirical evidence suitable for peer-reviewed publication       | Evaluation corpus anonymized per ADR-0031; results reproducible   |

### 3.3 Scope

| Dimension          | In scope                                                                        | Out of scope                                   |
| ------------------ | ------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Users**          | SRE, On-call Engineers, NOC, Support, Engineering leads                         | End users, customers                           |
| **Incident types** | Availability, latency, error rate, saturation incidents in cloud-native systems | Security incidents (SIEM/SOC), hardware faults |
| **Autonomy model** | HITL for production remediation; HOTL for detection and triage                  | Fully autonomous production remediation        |
| **Data sources**   | Prometheus metrics, Loki logs, Jaeger/Tempo traces, runbooks, post-mortems      | Real-time video, audio, end-user telemetry     |
| **Deployment env** | Single-cluster Kubernetes (staging + production) during research phase          | Multi-cloud, edge, on-premises                 |
| **Compliance**     | LGPD, GDPR, EU AI Act, OWASP LLM Top 10, SLSA Level 2, SOC 2 Type II principles | PCI-DSS full certification, SOC 2 audit        |

### 3.4 Stakeholders

| Role                 | Person / Group                     | Responsibility                                                  |
| -------------------- | ---------------------------------- | --------------------------------------------------------------- |
| Tech Lead / DPO      | Valdomiro de Oliveira Souza Júnior | Architecture decisions, privacy governance, dissertation author |
| Dissertation advisor | PPGCA/Unisinos faculty             | Academic review, RQ validation                                  |
| SRE persona (target) | On-call engineers (evaluated)      | Primary end-user of the Copilot                                 |

### 3.5 Constraints

| Constraint                  | Detail                                                                                          |
| --------------------------- | ----------------------------------------------------------------------------------------------- |
| **Research prototype**      | System is built to validate research hypotheses — not production-hardened beyond research scope |
| **No real PII in repo**     | RULE-C03: all evaluation data is anonymized per ADR-0031                                        |
| **LLM dependency**          | Anthropic Claude API (ADR-0003) — requires PII sanitization gate (ADR-0028) before every call   |
| **HITL mandatory**          | No autonomous PRODUCTION\_\* action without an ApprovalToken (ADR-0023)                         |
| **DPIA/RIPD gate**          | No production deployment without completed DPIA/RIPD (ADR-0029)                                 |
| **Spec-driven development** | No artifact without an approved spec (RULE-001); ADR before any architectural decision          |

---

## 4. Acceptance Criteria

- [ ] All four RQs (RQ1–RQ4) are traceable from this brief to at least one spec, ADR and evaluation criterion
- [ ] All five objectives (O1–O5) have a measurable outcome defined
- [ ] Scope table explicitly names what is out of scope (prevents scope creep in Phase 5)
- [ ] Constraints table references the ADR or RULE that enforces each constraint
- [ ] This document is reviewed and approved by the Tech Lead before any Phase 2 spec is authored
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                               |
| -------- | ----------------------------------------------------------------------- |
| ADR-0001 | C4 Model as the architecture documentation standard                     |
| ADR-0002 | Hexagonal architecture as the structural pattern for all agent services |
| ADR-0003 | LLM provider selection (Anthropic Claude Sonnet 4.6)                    |
| ADR-0004 | Multi-agent orchestration pattern (Orchestrator + 5 Specialists)        |
| ADR-0023 | HITL enforcement for all production remediation actions                 |
| ADR-0028 | PII sanitization gate before every LLM API call                         |
| ADR-0029 | DPIA/RIPD required before production deployment                         |

---

## References

- CLAUDE.md §1 — Project Vision and Success Criteria
- CLAUDE.md §5 RULE-001, RULE-002, RULE-003, RULE-005
- `specs/README.md` — spec hierarchy and ownership
- `docs/adr/README.md` — ADR index (ADR-0001 to ADR-0032)
- `issues.md` — implementation backlog phase structure
