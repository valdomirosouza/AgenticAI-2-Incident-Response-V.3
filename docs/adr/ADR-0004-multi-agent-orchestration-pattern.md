# ADR-0004: Multi-Agent Orchestration Pattern — Orchestrator + Specialists

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (system architecture), RQ3 (autonomy and guardrails), RQ4 (compliance)

---

## Context

The Incident Response Copilot must handle an incident lifecycle with five distinct
cognitive stages: Detection, Triage, Root Cause Analysis (RCA), Remediation and
Post-mortem. Each stage has different:

- **Data requirements** — Detection reads metrics; Triage reads alerts + logs; RCA
  reads traces + runbooks; Remediation writes to production systems; Post-mortem reads
  the full incident timeline.
- **Autonomy constraints** — Detection and Triage operate HOTL (agent acts, human
  monitors); Remediation is strictly HITL (human approves each action before execution).
- **Latency requirements** — Detection must be near-real-time (seconds); Post-mortem
  synthesis can tolerate minutes.
- **Failure modes** — A Remediation agent that hallucinates an action can cause
  production damage; a Detection agent that hallucinates only adds a false positive alert.

A monolithic agent that handles all stages is simpler to implement but:

- Cannot enforce stage-specific autonomy constraints (HITL vs. HOTL) cleanly.
- Couples failure domains — a hallucination in one stage can cascade.
- Cannot be tested in isolation per stage.
- Violates NIST AI RMF GOVERN-1.2 (assign roles and responsibilities for AI risk).

## Decision

We adopt an **Orchestrator + Specialist Agents** pattern as the multi-agent
orchestration architecture.

### Structure

```
OrchestratorAgent
├── DetectionAgent      (HOTL — reads Golden Signals, fires alert)
├── TriageAgent         (HOTL — scores severity, classifies, enriches)
├── RCAAgent            (HOTL — traces root cause, generates hypothesis)
├── RemediationAgent    (HITL — proposes action, awaits human approval)
└── PostMortemAgent     (HOTL — synthesises timeline, drafts report)
```

### Orchestrator responsibilities

- Receives normalized `IncidentEvent` from the ingestion pipeline.
- Maintains incident state machine (`DETECTED → TRIAGED → RCA_COMPLETE → REMEDIATED → CLOSED`).
- Routes to the appropriate specialist based on current incident state.
- Enforces autonomy mode: injects HITL gate before any `RemediationAgent` action
  execution; monitors (HOTL) all other specialist outputs.
- Holds the audit log: every specialist output and human decision is appended to the
  incident audit trail (`trace_id`-correlated).
- Handles specialist timeouts, retries and escalation to human operator.

### Specialist agent responsibilities

- Each specialist is a self-contained Hexagonal service (ADR-0002).
- Specialists communicate with the Orchestrator via typed messages (`IncidentContext`,
  `TriageResult`, `RCAHypothesis`, `RemediationProposal`, `PostMortemDraft`).
- Specialists do NOT communicate directly with each other — all routing passes through
  the Orchestrator. This enforces auditability: every inter-agent message is logged.
- Each specialist exposes a single inbound port: `execute(context) → result`.

### Guardrail attachment points

| Agent            | Autonomy | Guardrail                                                                                                      |
| ---------------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| DetectionAgent   | HOTL     | Rate limiter (max N alerts/min); deduplication window                                                          |
| TriageAgent      | HOTL     | Severity floor (cannot downgrade P1 without human confirmation)                                                |
| RCAAgent         | HOTL     | Confidence threshold gate (hypothesis below 0.6 → escalate)                                                    |
| RemediationAgent | HITL     | Hard stop — action proposal dispatched to approval queue; zero execution without explicit human approval token |
| PostMortemAgent  | HOTL     | PII scrubber before draft is persisted or shared                                                               |

### Inter-agent message bus

Messages are exchanged via an **in-process event bus** for the prototype (synchronous,
testable). A production deployment uses a durable message broker (Kafka or Pub/Sub —
to be decided in the infrastructure ADR, Phase 4). The OrchestratorAgent abstracts
the transport via a `MessageBusPort` outbound interface (ADR-0002).

## Alternatives Considered

| Alternative                            | Pros                                                                                                                   | Cons                                                                                                                                 |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Monolithic agent**                   | Simple; single context window; low latency                                                                             | Cannot enforce per-stage HITL/HOTL; single failure domain; hard to test stages in isolation                                          |
| **Peer-to-peer (fully decentralized)** | No single point of failure                                                                                             | No central audit log; HITL enforcement scattered across agents; very hard to reason about correctness                                |
| **Pipeline (linear chain)**            | Simple sequential execution                                                                                            | Rigid; no branching for escalation; parallel execution impossible                                                                    |
| **LangGraph (graph-based)**            | Rich state machine; built-in persistence; wide community                                                               | Framework lock-in; adds dependency on LangGraph versioning; architecture becomes implicit in graph config                            |
| **Orchestrator + Specialists** ✅      | Clear audit point; per-agent autonomy constraints; testable in isolation; replaces message bus without touching agents | Orchestrator is a potential bottleneck and single point of failure — mitigated by stateless design and incident-scoped instantiation |

## Consequences

**Positive:**

- HITL constraint is enforced at a single, auditable point (OrchestratorAgent) — no
  specialist can execute a remediation action without passing through the approval gate.
  Satisfies EU AI Act Arts. 9, 14 and NIST AI RMF GOVERN-1.
- Per-specialist failure isolation: a hallucination in TriageAgent does not affect
  RemediationAgent execution.
- Each specialist is independently testable, deployable and replaceable — supports the
  dissertation evaluation design (RQ3: can the system be validated stage by stage?).
- Full audit trail by construction: all inter-agent messages pass through Orchestrator
  and are logged with `trace_id` — satisfies SOC 2 CC7 and EU AI Act Art. 12.

**Negative / Trade-offs:**

- Orchestrator is a critical component — requires higher test coverage and resilience
  design than specialists.
- Inter-agent communication adds latency vs. a monolithic agent — acceptable because
  each stage's latency budget is separate (MTTD is dominated by Detection latency,
  not Orchestration overhead).
- More files and interfaces to maintain — justified by the compliance and testability
  requirements above.

## Review Criteria

Revisit this decision if:

- Orchestrator latency becomes a bottleneck in evaluation experiments (target: < 100ms
  routing overhead per transition).
- A framework (LangGraph, CrewAI, AutoGen) matures to the point where it implements
  this pattern natively with better persistence and observability than our bespoke
  implementation — evaluate framework adoption as a separate ADR.
- The number of specialist agents grows beyond 10 and the Orchestrator becomes a
  coordination bottleneck — consider a hierarchical orchestration pattern.

## References

- NIST AI RMF (2023) GOVERN-1 — Policies, processes and organizational roles
- EU AI Act (2024) Arts. 9, 12, 14 — Risk management, record-keeping, human oversight
- SOC 2 Type II CC7 — System monitoring
- `docs/adr/ADR-0002-hexagonal-architecture-agent-services.md` — Hexagonal structure for each specialist
- `docs/adr/ADR-0003-llm-provider-model-selection.md` — LLM used by specialists
- `specs/system/02-agent-design.md` — Agent design spec (to be authored, issue #9)
- `specs/system/03-incident-lifecycle.md` — Incident state machine (to be authored, issue #9)
- `skills/domain/agentic-ai-taxonomy.md` — Agentic AI terminology reference
- CLAUDE.md §1.3 — Autonomy model (HITL / HOTL)
