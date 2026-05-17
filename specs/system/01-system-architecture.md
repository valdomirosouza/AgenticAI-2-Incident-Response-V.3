# Spec 01: System Architecture

**Domain**: system
**Owner**: Tech Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #9
**Linked ADRs**: ADR-0001, ADR-0002
**Review cadence**: Every major release

---

## 1. Purpose

Define the system architecture of the Agentic AI Copilot using the C4 Model (ADR-0001)
and Hexagonal Architecture (ADR-0002). Establish the structural constraints that all
implementation specs must respect.

---

## 2. Context

The Copilot processes observability data (logs, metrics, traces) from a cloud-native
platform, reasons over it using an LLM, and produces human-readable triage summaries,
root cause hypotheses and—when approved—remediation actions. The architecture must:

- Keep domain logic isolated from infrastructure concerns (Hexagonal, ADR-0002)
- Provide a full audit trail for every agent decision (ADR-0024)
- Enforce PII sanitization before any data leaves the trust boundary (ADR-0028)
- Support blue-green deployments with rollback < 30s (ADR-0009)
- Expose enough structure for C4 diagrams that satisfy EU AI Act Art. 12 transparency

---

## 3. Decision

### 3.1 C4 Level 1 — System Context

```
┌──────────────────────────────────────────────────────────────────────┐
│                        System Context                                │
└──────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     incident alerts     ┌────────────────────────────┐
  │  On-call     │ ─────────────────────► │                            │
  │  Engineer    │ ◄───────── triage +     │   Agentic AI Copilot       │
  │  (SRE / NOC) │    remediation proposal │   (this system)            │
  └──────────────┘                         │                            │
                                           └──────┬──────────┬──────────┘
                                                  │          │
                          observability data       │          │ LLM prompts
                          (logs, metrics, traces)  │          │ (PII sanitized)
                                                  ▼          ▼
                                    ┌─────────────────┐  ┌──────────────────┐
                                    │  Observability  │  │  Anthropic       │
                                    │  Stack          │  │  Claude API      │
                                    │  (Prometheus /  │  │  (External)      │
                                    │   Loki / Tempo) │  └──────────────────┘
                                    └─────────────────┘
```

**External systems:**

| System              | Type     | Direction     | Data transferred                        | ADR                          |
| ------------------- | -------- | ------------- | --------------------------------------- | ---------------------------- |
| Anthropic Claude    | External | Outbound      | Sanitized prompt text (no PII)          | ADR-0003, ADR-0028, ADR-0032 |
| Observability Stack | Internal | Inbound       | Logs, metrics, traces (may contain PII) | ADR-0011–ADR-0015            |
| HashiCorp Vault     | Internal | Inbound       | Secrets, API keys, HITL signing key     | ADR-0020                     |
| On-call Engineer    | Human    | Bidirectional | Alerts in, approvals out (HITL)         | ADR-0023                     |

### 3.2 C4 Level 2 — Container Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Agentic AI Copilot                               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  API Layer  (FastAPI / REST + WebSocket)                        │    │
│  │  · POST /incidents/{id}/analyze                                 │    │
│  │  · POST /incidents/{id}/approve  (HITL endpoint)               │    │
│  │  · GET  /incidents/{id}/audit-trail                             │    │
│  └───────────────────────────┬─────────────────────────────────────┘    │
│                              │                                          │
│  ┌───────────────────────────▼─────────────────────────────────────┐    │
│  │  Orchestrator Agent  (domain layer)                             │    │
│  │  · Routes to specialist agents                                  │    │
│  │  · Enforces HITL gate before any PRODUCTION_* action            │    │
│  │  · Writes every decision to Audit Trail                         │    │
│  └──┬──────────┬────────────┬──────────────┬──────────────┬────────┘    │
│     │          │            │              │              │             │
│  ┌──▼──┐  ┌───▼───┐  ┌─────▼───┐  ┌───────▼──┐  ┌───────▼────┐       │
│  │Detec│  │Triage │  │  RCA    │  │Remediati │  │PostMortem  │       │
│  │tion │  │ Agent │  │  Agent  │  │on Agent  │  │  Agent     │       │
│  │Agent│  │(HOTL) │  │  (HOTL) │  │(HITL)    │  │(HOTL)      │       │
│  └──┬──┘  └───┬───┘  └─────┬───┘  └───────┬──┘  └───────┬────┘       │
│     └─────────┴────────────┴──────────────┴──────────────┘            │
│                              │                                          │
│  ┌───────────────────────────▼─────────────────────────────────────┐    │
│  │  Ports & Adapters  (infrastructure layer)                       │    │
│  │  · ObservabilityPort → PromQL / LogQL / TraceQL adapters        │    │
│  │  · LLMPort          → Anthropic adapter (+ PII sanitizer)       │    │
│  │  · AuditPort        → Append-only hash-chain store              │    │
│  │  · HITLPort         → ApprovalToken validator (Vault-signed)    │    │
│  │  · SecretsPort      → Vault agent sidecar                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Hexagonal Architecture constraints

Per ADR-0002:

| Layer       | May import from        | May NOT import from                    |
| ----------- | ---------------------- | -------------------------------------- |
| `domain/`   | Nothing outside domain | `adapters/`, `api/`, `infrastructure/` |
| `ports/`    | `domain/`              | `adapters/`, `infrastructure/`         |
| `adapters/` | `ports/`, `domain/`    | Other `adapters/`                      |
| `api/`      | `ports/`, `domain/`    | `adapters/` (directly)                 |

Enforced by `import-linter` in the PR gate (ADR-0007 G09).

### 3.4 Data flow — PII boundary

```
Observability Stack
        │
        │ raw data (may contain PII)
        ▼
  OTel SpanProcessor  ──── PII masking (ADR-0014) ────► masked observability data
        │
        │ masked data
        ▼
  Orchestrator Agent
        │
        │ prompt construction
        ▼
  PII Sanitizer (Presidio)  ──── ADR-0028 ────► sanitized prompt
        │
        │ sanitized prompt (no PII)
        ▼
  Anthropic Claude API  (cross-border transfer — ADR-0032)
```

The PII sanitization operates at two layers (defence in depth):

1. **OTel layer** — masks PII before it enters the observability pipeline (ADR-0014)
2. **LLM adapter layer** — Presidio sanitization before every API call (ADR-0028)

### 3.5 Deployment topology

Single Kubernetes cluster with two namespaces:

| Namespace       | Purpose                                  |
| --------------- | ---------------------------------------- |
| `copilot`       | API, OrchestratorAgent, SpecialistAgents |
| `observability` | Prometheus, Loki, Tempo, Grafana         |

Blue-green deployment via Argo Rollouts (ADR-0009). Vault runs as a sidecar per ADR-0020.

### 3.6 Architectural constraints register

| Constraint ID | Constraint                                                 | Enforced by                                |
| ------------- | ---------------------------------------------------------- | ------------------------------------------ |
| AC-01         | Domain layer has zero imports from adapters                | import-linter, G09                         |
| AC-02         | No prompt dispatched to LLM without `sanitized=True`       | PiiSanitizationRequired exception, Semgrep |
| AC-03         | No PRODUCTION\_\* action without a valid ApprovalToken     | action_executor validation, ADR-0023       |
| AC-04         | Every agent decision written to append-only audit trail    | AuditPort, ADR-0024                        |
| AC-05         | No secret stored in env vars, files or repository          | Vault sidecar, Semgrep rule, ADR-0020      |
| AC-06         | All cross-border transfers documented in transfer register | ADR-0032                                   |

---

## 4. Acceptance Criteria

- [ ] C4 Level 1 (System Context) and Level 2 (Container) diagrams are present in this spec
- [ ] All external system dependencies are identified with data direction and ADR reference
- [ ] Hexagonal Architecture layer constraints table is complete with import rules
- [ ] PII boundary data flow diagram shows both OTel and LLM adapter sanitization layers
- [ ] Architectural constraints register (AC-01 to AC-06) covers all hard gates
- [ ] Deployment topology defines at minimum two namespaces and blue-green strategy
- [ ] Reviewed by Tech Lead before Phase 3 implementation begins
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                              |
| -------- | ---------------------------------------------------------------------- |
| ADR-0001 | C4 Model — documentation standard for all architecture diagrams        |
| ADR-0002 | Hexagonal Architecture — structural pattern; import-linter enforcement |
| ADR-0003 | LLM provider selection — Anthropic Claude Sonnet 4.6                   |
| ADR-0009 | Blue-green deployment strategy                                         |
| ADR-0011 | Golden Signals canonical metric set                                    |
| ADR-0012 | OpenTelemetry instrumentation standard                                 |
| ADR-0014 | PII masking in observability pipelines (OTel layer)                    |
| ADR-0020 | Zero-trust secrets management via HashiCorp Vault                      |
| ADR-0023 | HITL enforcement — ApprovalToken gate for PRODUCTION\_\* actions       |
| ADR-0024 | Immutable agent audit trail — append-only hash chain                   |
| ADR-0028 | PII sanitization before LLM API calls (adapter layer)                  |
| ADR-0032 | Cross-border data transfer safeguards                                  |

---

## References

- CLAUDE.md §1.3 System Boundaries
- CLAUDE.md §1.4 Architecture Pillars
- `docs/adr/ADR-0001-c4-model-architecture-documentation.md`
- `docs/adr/ADR-0002-hexagonal-architecture-agent-services.md`
- `specs/system/00-project-brief.md` — scope and constraints
- `specs/system/02-agent-design.md` — agent roles and orchestration detail
