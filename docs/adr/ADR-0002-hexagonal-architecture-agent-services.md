# ADR-0002: Hexagonal Architecture as Structural Pattern for Agent Services

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (system architecture), RQ3 (guardrails and autonomy controls)

---

## Context

Each agent service in the Copilot (DetectionAgent, TriageAgent, RemediationAgent,
PostMortemAgent) must satisfy four conflicting pressures simultaneously:

1. **Testability** — agent logic must be testable in isolation, without live observability
   backends, LLM APIs or databases. RULE-C02 forbids synthetic fixtures: tests must use
   real corpus data, meaning the test harness substitutes infrastructure, not data.
2. **Portability** — the system must be demonstrable on a laptop (research prototype)
   and deployable to cloud (Kubernetes/GCP). Infrastructure details must not bleed into
   domain logic.
3. **Replaceability** — LLM provider, vector store, message broker and observability
   backend are all subject to change as the research evolves. Swapping one must not
   require touching agent logic.
4. **Auditability** — EU AI Act Arts. 9 and 12 require that every agent action be
   logged and traceable. All I/O crossing a system boundary must pass through a
   controlled, observable interface.

A layered architecture (traditional n-tier) satisfies testability but couples
infrastructure details into layers; Clean Architecture satisfies replaceability but
introduces excessive abstractions for a research prototype. Hexagonal Architecture
(Ports and Adapters) satisfies all four requirements with minimal abstraction overhead.

## Decision

We adopt **Hexagonal Architecture** (Alistair Cockburn, 2005 — also known as Ports and
Adapters) as the structural pattern for all agent services.

Structure per agent service:

```
src/agents/<agent-name>/
├── domain/          # Pure domain logic — no imports from infrastructure/
│   ├── models/      # Domain entities (Incident, Alert, RemediationAction)
│   └── services/    # Domain services (detection rules, triage scoring, RCA logic)
├── ports/           # Interfaces (abstract classes / protocols)
│   ├── inbound/     # Driving ports — what the outside world calls into the agent
│   └── outbound/    # Driven ports — what the agent calls out to
└── adapters/        # Concrete implementations of ports
    ├── inbound/     # HTTP handlers, gRPC stubs, event consumers
    └── outbound/    # LLM client, metrics backend, runbook store, DB repository
```

**Mandatory rules derived from this pattern:**

- `domain/` has zero imports from `adapters/` or any external library (enforced by
  import linter in `harness/code-check.yml`).
- All cross-boundary I/O (LLM calls, DB writes, metric reads) passes through a Port
  interface — never called directly from domain logic.
- Each Port interface is the unit of auditability: every call is logged with `trace_id`
  and `span_id` (OpenTelemetry) before execution.
- Test doubles (fakes, stubs) implement Port interfaces — domain tests never mock
  infrastructure directly.

## Alternatives Considered

| Alternative                         | Pros                                                                                                                       | Cons                                                                                              |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Layered (n-tier)**                | Simple, familiar, low boilerplate                                                                                          | Infrastructure details leak into service layer; hard to swap LLM or DB without touching logic     |
| **Clean Architecture**              | Strong separation, well-documented                                                                                         | Use Case / Entity distinction adds indirection that is unnecessary at research-prototype scale    |
| **Hexagonal (Ports & Adapters)** ✅ | Clean domain/infrastructure boundary; minimal overhead; natural fit for agent services with multiple external dependencies | Requires discipline to maintain port boundaries; import linter needed to enforce rules            |
| **No explicit architecture**        | Zero overhead                                                                                                              | Domain and infra couple immediately; untestable without live systems; fails EU AI Act audit trail |
| **CQRS + Event Sourcing**           | Strong audit trail, scalable                                                                                               | Very high complexity for a research prototype; premature optimisation                             |

## Consequences

**Positive:**

- Agent domain logic is fully testable without LLM API, Prometheus, or database — CI
  runs fast and deterministically.
- LLM provider can be swapped by writing a new `outbound/llm_adapter.py` that
  implements the `LLMPort` interface — zero changes to domain logic.
- All outbound calls pass through ports → all calls are intercepted by OpenTelemetry
  instrumentation → complete audit trail by construction, satisfying EU AI Act Art. 12.
- SOC 2 CC6 (Logical access controls): each Port interface enforces the boundary at
  which HITL checks are applied — guardrails attach to ports, not scattered across logic.

**Negative / Trade-offs:**

- Requires defining Port interfaces before writing adapters — a discipline overhead
  that pays off only if the system is tested or the infrastructure actually changes.
- Import linter rule (`domain/` must not import `adapters/`) requires tooling setup
  (configured in `harness/code-check.yml` — issue #21).
- Junior contributors unfamiliar with Ports and Adapters need onboarding; mitigated
  by `skills/engineering/` documentation and this ADR.

## Review Criteria

Revisit this decision if:

- The number of agent services grows beyond 10 and the Port-per-service abstraction
  creates significant duplication — consider a shared infrastructure layer.
- The research prototype requires rapid iteration speed that the port interface
  discipline slows down significantly.
- A framework (LangGraph, CrewAI) is chosen (ADR-0004) that imposes its own
  architectural constraints incompatible with this pattern.

## References

- Cockburn, A. (2005). _Hexagonal Architecture_. alistair.cockburn.us
- Evans, E. (2003). _Domain-Driven Design_. Addison-Wesley. (Port terminology context)
- EU AI Act (2024) Arts. 9, 12 — Risk management and record-keeping requirements
- SOC 2 Type II, CC6 — Logical and physical access controls
- `docs/adr/ADR-0004-multi-agent-orchestration-pattern.md` — agent structure depends on this ADR
- `specs/system/02-agent-design.md` — agent service spec (to be authored, issue #9)
- CLAUDE.md §1.4, §7 — Architecture pillars and directory structure
