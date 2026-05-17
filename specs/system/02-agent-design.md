# Spec 02: Agent Design

**Domain**: system
**Owner**: Tech Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #9
**Linked ADRs**: ADR-0003, ADR-0004
**Review cadence**: Every major release or on model change

---

## 1. Purpose

Define the roles, responsibilities, orchestration pattern and autonomy levels of each
agent in the Copilot. Establish HITL/HOTL trigger conditions per agent and action type.

---

## 2. Context

The Copilot is composed of one OrchestratorAgent and five SpecialistAgents (ADR-0004).
Each specialist handles one stage of the incident lifecycle. Autonomy levels differ by
stage: detection and triage are low-risk (HOTL); remediation is high-risk (HITL).

All agents share:

- LLM inference via Anthropic Claude Sonnet 4.6 (ADR-0003), with Haiku fallback
- PII sanitization before every LLM call (ADR-0028)
- Structured output validated by Pydantic schemas (OWASP LLM05 mitigation, ADR-0021)
- Decision written to the audit trail (ADR-0024) before any action is taken
- Confidence threshold ≥ 0.6 for any automated output labelled `AI-GENERATED` (ADR-0021)

---

## 3. Decision

### 3.1 Agent roster

| Agent                 | Role                                                                        | Autonomy | LLM model  |
| --------------------- | --------------------------------------------------------------------------- | -------- | ---------- |
| **OrchestratorAgent** | Routes incidents to specialists; manages state machine; enforces HITL gate  | HOTL     | Sonnet 4.6 |
| **DetectionAgent**    | Correlates Golden Signals anomalies; fires `incident.created` event         | HOTL     | Haiku 4.5  |
| **TriageAgent**       | Classifies severity (P1–P4); identifies affected CUJs; notifies on-call     | HOTL     | Sonnet 4.6 |
| **RCAAgent**          | Constructs causal hypothesis from logs/traces; scores root cause confidence | HOTL     | Sonnet 4.6 |
| **RemediationAgent**  | Proposes and (after HITL approval) executes remediation actions             | **HITL** | Sonnet 4.6 |
| **PostMortemAgent**   | Drafts blameless post-mortem from incident timeline                         | HOTL     | Sonnet 4.6 |

### 3.2 Orchestrator state machine

```
         ┌───────────────────────────────────────────┐
         │            OrchestratorAgent               │
         │                                           │
  alert  │   IDLE ──► DETECTING ──► TRIAGING         │
 ───────►│               │              │            │
         │               │ anomaly      │ severity   │
         │               ▼ confirmed    ▼ classified │
         │          INVESTIGATING ──► PROPOSING      │
         │               │              │            │
         │            RCA done       HITL gate       │
         │                              │            │
         │                         ┌───▼───┐         │
         │                         │PENDING│         │
         │                         │APPROVAL│        │
         │                         └───┬───┘         │
         │                    approved │ rejected     │
         │                             ▼      ▼      │
         │                      REMEDIATING ESCALATED│
         │                             │             │
         │                          resolved         │
         │                             ▼             │
         │                     POST_MORTEM ──► CLOSED│
         └───────────────────────────────────────────┘
```

State transitions are persisted to the audit trail (ADR-0024) at every step.

### 3.3 HITL / HOTL trigger matrix

| Agent             | Action type             | Autonomy | Trigger condition                                      |
| ----------------- | ----------------------- | -------- | ------------------------------------------------------ |
| DetectionAgent    | `incident.created`      | HOTL     | Automated; engineer notified, not required to approve  |
| TriageAgent       | `incident.severity_set` | HOTL     | Automated; engineer may override via API               |
| TriageAgent       | `on_call.notified`      | HOTL     | Automated PagerDuty/Slack message                      |
| RCAAgent          | `rca.hypothesis_set`    | HOTL     | Automated; confidence score shown; engineer may reject |
| RemediationAgent  | `PRODUCTION_*`          | **HITL** | **Blocked until ApprovalToken received (ADR-0023)**    |
| RemediationAgent  | `remediation.proposed`  | HOTL     | Proposal displayed; engineer reviews before approving  |
| OrchestratorAgent | `incident.escalated`    | HOTL     | Auto-escalate on timeout; engineer override available  |
| PostMortemAgent   | `postmortem.drafted`    | HOTL     | Draft surfaced for human review before publication     |

**HITL timeout policy** (per ADR-0023):

| Severity | Approval window | On timeout                |
| -------- | --------------- | ------------------------- |
| P1       | 5 minutes       | Escalate; NO auto-execute |
| P2       | 15 minutes      | Escalate; NO auto-execute |
| P3/P4    | 60 minutes      | Escalate; NO auto-execute |

Auto-execution on timeout is **explicitly prohibited** (ADR-0023 §decision).

### 3.4 Message schema

All inter-agent messages are typed `AgentMessage` Pydantic models:

```python
class AgentMessage(BaseModel):
    message_id: UUID
    incident_id: str
    source_agent: AgentRole
    target_agent: AgentRole
    message_type: MessageType        # one of: ANALYZE, TRIAGE, RCA, PROPOSE, APPROVE, REJECT, DRAFT
    payload: dict                    # validated against message_type-specific schema
    trace_id: str                    # W3C TraceContext propagated from incoming request
    span_id: str
    timestamp: datetime
    confidence: float | None         # required for PROPOSE and RCA message types
```

Unrecognized message types are rejected with `UnknownMessageTypeError` — never silently
dropped or forwarded.

### 3.5 LLM interaction constraints

Per ADR-0003 and ADR-0021:

| Constraint                                | Enforcement                                                          |
| ----------------------------------------- | -------------------------------------------------------------------- |
| All prompts PII-sanitized before dispatch | `PiiSanitizationRequired` exception in LLMAdapter (ADR-0028)         |
| All responses schema-validated            | Pydantic model; validation failure → ESCALATE, not guess             |
| Confidence threshold ≥ 0.6                | Checked before writing hypothesis to audit trail                     |
| Outputs labelled `AI-GENERATED`           | Injected by OrchestratorAgent before surfacing to engineer           |
| Model: `claude-sonnet-4-6`                | Default; `claude-haiku-4-5-20251001` for DetectionAgent latency path |
| Fallback on LLM error                     | Escalate to on-call; do not guess or silently degrade                |

### 3.6 Privacy Impact

- Agent prompts contain sanitized observability data — no raw PII per ADR-0028.
- LLM responses may not be cached to disk per ADR-0030 (session memory only).
- Agent decision payloads written to audit trail use pseudonymised role labels, not
  engineer names, per ADR-0010 (blameless post-mortem format).
- TriageAgent and RCAAgent are subject to quarterly bias audits (ADR-0026).

---

## 4. Acceptance Criteria

- [ ] All 6 agents (Orchestrator + 5 Specialists) are described with role, autonomy level and LLM model
- [ ] Orchestrator state machine covers all 8 states: IDLE → DETECTING → TRIAGING → INVESTIGATING → PROPOSING → PENDING_APPROVAL → REMEDIATING/ESCALATED → POST_MORTEM → CLOSED
- [ ] HITL/HOTL trigger matrix is complete for every action type produced by every agent
- [ ] HITL timeout policy is defined with explicit "NO auto-execute on timeout" for all severities
- [ ] `AgentMessage` schema includes all mandatory fields: message_id, incident_id, source/target agents, message_type, payload, trace_id, span_id, timestamp, confidence
- [ ] LLM interaction constraints table references ADR-0003, ADR-0021, ADR-0028
- [ ] Privacy Impact section documents pseudonymisation and bias audit obligations
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                             |
| -------- | --------------------------------------------------------------------- |
| ADR-0003 | LLM provider — Anthropic Claude Sonnet 4.6; Haiku fallback            |
| ADR-0004 | Multi-agent orchestration pattern (Orchestrator + 5 Specialists)      |
| ADR-0010 | Blameless post-mortem format — pseudonymised roles in PostMortemAgent |
| ADR-0021 | OWASP LLM Top 10 checklist — LLM01/LLM05/LLM06 mitigations            |
| ADR-0023 | HITL enforcement — ApprovalToken; timeout policy; no auto-execute     |
| ADR-0024 | Immutable audit trail — every state transition logged                 |
| ADR-0026 | Quarterly bias audit for TriageAgent and RCAAgent                     |
| ADR-0028 | PII sanitization before every LLM prompt dispatch                     |
| ADR-0030 | LLM prompt/response never persisted to disk                           |

---

## References

- CLAUDE.md §1.3 System Boundaries (autonomy model)
- CLAUDE.md §4.2 Canonical Glossary (HITL, HOTL, Guardrail definitions)
- `specs/system/01-system-architecture.md` — container diagram and AC-03 constraint
- `specs/system/03-incident-lifecycle.md` — lifecycle stages mapped to agent handoffs
- `specs/ethics/16-autonomy-boundaries.md` — HITL/HOTL policy specification
