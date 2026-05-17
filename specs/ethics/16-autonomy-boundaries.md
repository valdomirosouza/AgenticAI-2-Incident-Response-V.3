# Spec 16: Autonomy Boundaries

**Domain**: ethics
**Owner**: Tech Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #13
**Linked ADRs**: ADR-0023, ADR-0025
**Review cadence**: Semi-annually or on model change; Ethics reviewer + Legal required

---

## 1. Purpose

Define what agents can and cannot do without human approval. Provide the complete
action-type × autonomy-level × HITL-trigger matrix that governs every agent action
in the Copilot. This spec is the direct prerequisite for HITL guardrail implementation
in Phase 5.

---

## 2. Context

CLAUDE.md §1.6 criterion 6 is a hard gate: HITL controls must be active for all
autonomous remediation actions in production. EU AI Act Art. 14 requires meaningful
human oversight for high-risk AI systems. NIST AI RMF GOVERN-5 requires documented
autonomy constraints.

The Copilot spans a spectrum from fully automated detection (HOTL — low risk) to
production remediation (HITL — high risk). Without a precise boundary map, developers
may inadvertently create autonomous paths that bypass HITL, or over-restrict the agent
in ways that negate its MTTD/MTTR benefit.

---

## 3. Decision

### 3.1 Autonomy level definitions

| Level       | Definition                                                                    | Human role                               |
| ----------- | ----------------------------------------------------------------------------- | ---------------------------------------- |
| **HOTL**    | Human-on-the-Loop — agent acts automatically; human monitors and can override | Notified; may intervene at any time      |
| **HITL**    | Human-in-the-Loop — agent proposes; action blocked until human approves       | Must explicitly approve before execution |
| **BLOCKED** | Action is prohibited regardless of approval                                   | N/A — architectural limit                |

### 3.2 Full action-type × autonomy matrix

| Action type                   | Agent             | Autonomy    | HITL trigger condition                                          | Timeout policy                      |
| ----------------------------- | ----------------- | ----------- | --------------------------------------------------------------- | ----------------------------------- |
| `incident.created`            | DetectionAgent    | HOTL        | No approval needed; engineer notified via PagerDuty/Slack       | —                                   |
| `incident.severity_set`       | TriageAgent       | HOTL        | No approval needed; engineer may override via API               | —                                   |
| `on_call.notified`            | TriageAgent       | HOTL        | Automated PagerDuty/Slack message sent                          | —                                   |
| `rca.hypothesis_set`          | RCAAgent          | HOTL        | No approval needed; confidence shown; engineer may reject       | —                                   |
| `remediation.proposed`        | RemediationAgent  | HOTL        | Proposal displayed to engineer for review                       | —                                   |
| `PRODUCTION_pod_restart`      | RemediationAgent  | **HITL**    | ApprovalToken required (ADR-0023)                               | P1: 5 min / P2: 15 min / P3: 60 min |
| `PRODUCTION_config_change`    | RemediationAgent  | **HITL**    | ApprovalToken required (ADR-0023)                               | P1: 5 min / P2: 15 min / P3: 60 min |
| `PRODUCTION_scale_up`         | RemediationAgent  | **HITL**    | ApprovalToken required (ADR-0023)                               | P1: 5 min / P2: 15 min / P3: 60 min |
| `PRODUCTION_scale_down`       | RemediationAgent  | **HITL**    | ApprovalToken required (ADR-0023)                               | P1: 5 min / P2: 15 min / P3: 60 min |
| `PRODUCTION_traffic_shift`    | RemediationAgent  | **HITL**    | ApprovalToken required (ADR-0023)                               | P1: 5 min / P2: 15 min / P3: 60 min |
| `PRODUCTION_db_query`         | RemediationAgent  | **HITL**    | ApprovalToken required (ADR-0023)                               | P1: 5 min / P2: 15 min / P3: 60 min |
| `PRODUCTION_secret_rotation`  | RemediationAgent  | **HITL**    | ApprovalToken required (ADR-0023)                               | P1: 5 min / P2: 15 min / P3: 60 min |
| `incident.escalated`          | OrchestratorAgent | HOTL        | Auto-escalate on timeout; engineer override available           | —                                   |
| `postmortem.drafted`          | PostMortemAgent   | HOTL        | Draft surfaced for human review before publication              | —                                   |
| `agent.kill_switch_activated` | OrchestratorAgent | HOTL        | Triggered by engineer or automatic threshold breach (ADR-0025)  | —                                   |
| `PRODUCTION_data_delete`      | Any               | **BLOCKED** | Prohibited in all circumstances — no approval path exists       | N/A                                 |
| `PRODUCTION_iam_change`       | Any               | **BLOCKED** | Prohibited — IAM changes require separate change management     | N/A                                 |
| `PRODUCTION_firewall_change`  | Any               | **BLOCKED** | Prohibited — network changes require separate change management | N/A                                 |

### 3.3 HITL timeout protocol

On HITL approval timeout, the action is **never auto-executed**. The Orchestrator:

1. Emits `hitl.approval_expired` audit event (ADR-0024).
2. Escalates incident severity by one level (P2 → P1, P3 → P2).
3. Pages backup on-call engineer.
4. Presents the same approval request with the new severity to the backup on-call.
5. If the backup window also expires: incident escalated to Engineering Lead; remediation
   path frozen; no further automated proposals until a human manually resumes.

Auto-execution on timeout is **explicitly prohibited** — hardcoded in
`action_executor.py`, tested by a dedicated unit test that simulates a timeout and
asserts no production action is taken.

### 3.4 ApprovalToken specification

Per ADR-0023, every HITL-gated action requires a cryptographically signed ApprovalToken:

```python
class ApprovalToken(BaseModel):
    token_id: UUID               # unique per approval request
    incident_id: str
    action_type: str             # must match the PRODUCTION_* action being approved
    approver_role: str           # role of the engineer granting approval
    approved_at: datetime        # UTC timestamp of approval
    expires_at: datetime         # approved_at + P-severity window
    signature: str               # HMAC-SHA256(token_id|incident_id|action_type|approved_at, Vault S-02)
```

Validation in `action_executor.execute()` checks (in order):

1. Signature valid against Vault key S-02.
2. Token not expired (`expires_at > now()`).
3. `action_type` in token matches the action being requested.
4. `approver_role` is an authorised approver role.

Any validation failure → action rejected; `hitl.validation_failed` audit event written.

### 3.5 BLOCKED action enforcement

BLOCKED actions are prevented at multiple layers:

| Layer         | Enforcement mechanism                                                  |
| ------------- | ---------------------------------------------------------------------- |
| Domain layer  | `RemediationAgent` raises `BlockedActionError` for any BLOCKED type    |
| Adapter layer | `action_executor` has no implementation for BLOCKED action types       |
| SAST          | Semgrep rule `hitl-bypass` detects any call path to BLOCKED types      |
| Test          | Unit test asserts `BlockedActionError` is raised for all BLOCKED types |

### 3.6 EU AI Act Art. 14 compliance

This spec satisfies EU AI Act Art. 14 (human oversight) requirements:

| Art. 14 requirement                       | Implementation                                                          |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| Override capability at any time           | Engineer can reject any HITL proposal; kill-switch available (ADR-0025) |
| Monitoring capability during operation    | HOTL for detection/triage/RCA — all decisions surfaced in real time     |
| Understanding of system capabilities      | Confidence scores + `AI-GENERATED` labels on all outputs (ADR-0021)     |
| Ability to disregard, override or reverse | Remediation rejection returns to human-managed workflow                 |
| Not overriding human oversight            | No auto-execute on timeout; BLOCKED actions are architectural limits    |

---

## 4. Acceptance Criteria

- [ ] Autonomy matrix covers all action types including BLOCKED category
- [ ] HITL timeout protocol specifies no auto-execute and documents escalation path
- [ ] ApprovalToken schema includes all 7 fields; validation order documented
- [ ] BLOCKED action enforcement documented at all 4 layers (domain, adapter, SAST, test)
- [ ] EU AI Act Art. 14 compliance table covers all 5 requirements
- [ ] Ethics reviewer + Legal review recorded before merge
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                       |
| -------- | --------------------------------------------------------------- |
| ADR-0004 | Multi-agent orchestration — HITL/HOTL agent assignments         |
| ADR-0021 | OWASP LLM06 Excessive Agency — confidence labels, HITL gate     |
| ADR-0023 | HITL cryptographic enforcement — ApprovalToken, timeout policy  |
| ADR-0024 | Immutable audit trail — `hitl.*` event types                    |
| ADR-0025 | Kill-switch — override capability required by EU AI Act Art. 14 |

---

## References

- CLAUDE.md §1.6 criterion 6 (HITL in production — hard gate)
- CLAUDE.md §4.2 Canonical Glossary (HITL, HOTL definitions)
- EU AI Act (2024) Art. 14 — Human oversight
- NIST AI RMF GOVERN-5 — Organizational risk tolerance
- `specs/system/02-agent-design.md` — HITL/HOTL trigger matrix (system-level view)
- `specs/ethics/17-audit-trail.md` — `hitl.*` events logged to audit trail
