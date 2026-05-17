# Skill: Agentic Ethics

**Domain**: ethics
**Activation triggers**: agent autonomy, delegation limits, value alignment, HITL, HOTL, BLOCKED actions, kill-switch, ApprovalToken, action executor, autonomy boundaries, EU AI Act Art. 14
**References**: specs/ethics/16-autonomy-boundaries.md, ADR-0023, ADR-0025

---

## Autonomy Level Definitions

| Level       | Definition                                                                    | Human role                               |
| ----------- | ----------------------------------------------------------------------------- | ---------------------------------------- |
| **HOTL**    | Human-on-the-Loop — agent acts automatically; human monitors and can override | Notified; may intervene at any time      |
| **HITL**    | Human-in-the-Loop — agent proposes; action blocked until human approves       | Must explicitly approve before execution |
| **BLOCKED** | Action is prohibited regardless of approval — no path exists                  | N/A — architectural limit                |

---

## Full Action-Type × Autonomy Matrix (spec 16)

| Action type                   | Agent             | Autonomy    | Trigger / Condition                                             | Timeout policy                      |
| ----------------------------- | ----------------- | ----------- | --------------------------------------------------------------- | ----------------------------------- |
| `incident.created`            | DetectionAgent    | HOTL        | Engineer notified via PagerDuty/Slack; no approval needed       | —                                   |
| `incident.severity_set`       | TriageAgent       | HOTL        | Engineer may override via API                                   | —                                   |
| `on_call.notified`            | TriageAgent       | HOTL        | Automated PagerDuty/Slack message sent                          | —                                   |
| `rca.hypothesis_set`          | RCAAgent          | HOTL        | Confidence shown; engineer may reject                           | —                                   |
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

---

## ApprovalToken Specification (ADR-0023)

Every HITL-gated action requires a cryptographically signed `ApprovalToken`:

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

Validation in `action_executor.execute()` — checks in order:

1. Signature valid against Vault key `S-02`
2. Token not expired (`expires_at > now()`)
3. `action_type` in token matches the action being requested
4. `approver_role` is an authorised approver role

Any validation failure → action rejected; `hitl.validation_failed` audit event written.

---

## HITL Timeout Protocol

On approval timeout, the action is **never auto-executed**:

1. Emit `hitl.approval_expired` audit event (ADR-0024)
2. Escalate incident severity one level (P2 → P1, P3 → P2)
3. Page backup on-call engineer
4. Present the same approval request with new severity to the backup on-call
5. If backup window also expires: escalate to Engineering Lead; freeze remediation path; no further automated proposals until a human manually resumes

**Auto-execution on timeout is explicitly prohibited** — hardcoded in `action_executor.py`, tested by a dedicated unit test that simulates timeout and asserts no production action is taken.

---

## BLOCKED Action Enforcement (4 Layers)

| Layer         | Enforcement mechanism                                                  |
| ------------- | ---------------------------------------------------------------------- |
| Domain layer  | `RemediationAgent` raises `BlockedActionError` for any BLOCKED type    |
| Adapter layer | `action_executor` has no implementation for BLOCKED action types       |
| SAST          | Semgrep rule `hitl-bypass` detects any call path to BLOCKED types      |
| Test          | Unit test asserts `BlockedActionError` is raised for all BLOCKED types |

```python
# Domain layer enforcement
class RemediationAgent:
    BLOCKED_ACTION_TYPES = {
        "PRODUCTION_data_delete",
        "PRODUCTION_iam_change",
        "PRODUCTION_firewall_change",
    }

    def propose(self, action_type: str, ...) -> RemediationProposal:
        if action_type in self.BLOCKED_ACTION_TYPES:
            raise BlockedActionError(
                f"{action_type} is a BLOCKED action type — "
                "no approval path exists (spec 16 §3.5)"
            )
        ...
```

---

## Kill-Switch Protocol (ADR-0025)

**Trigger conditions** (any one sufficient):

- Engineer manual activation via authenticated API endpoint
- Automatic: 3+ `hitl.validation_failed` events within 5 minutes
- Automatic: `audit.write_failed` event (audit trail failure = halt all agent actions)
- Automatic: kill-switch threshold breach configured in `OrchestratorAgent`

**Activation sequence (RTO < 60 seconds):**

```
1. OrchestratorAgent → send SIGTERM to all specialist agents (< 5s)
2. Vault → revoke all agent service account tokens (< 15s)
3. OrchestratorAgent → emit agent.kill_switch_activated audit event (< 20s)
4. Alert PagerDuty P1: "Copilot kill-switch activated — manual incident response required"
5. All PRODUCTION_* adapters refuse all calls (no valid Vault token)
```

**Quarterly drill requirement**: kill-switch drill must be run every quarter (same cadence as bias audit). Drill must achieve RTO < 60s and produce a passing `agent.kill_switch_activated` audit event.

**Recovery from kill-switch**: manual procedure, requires Engineering Lead approval. Not automated — the kill-switch is a one-way gate until a human decision to resume.

---

## Adding a New Action Type

When adding a new agent action type, this checklist must pass before the PR is merged:

- [ ] Action type classified in the HITL/HOTL/BLOCKED matrix (spec 16 §3.2)
- [ ] If HITL: `ApprovalToken` flow implemented in `action_executor.execute()`
- [ ] If HITL: timeout policy documented (P1/P2/P3 windows)
- [ ] If BLOCKED: `BlockedActionError` raised in `RemediationAgent` for this type
- [ ] If BLOCKED: `action_executor` has no implementation for this type
- [ ] Semgrep rule `hitl-bypass` (G07) still catches direct adapter calls
- [ ] Unit test covers the new action type in the autonomy matrix
- [ ] New action type added to audit trail vocabulary (spec 17 §3.3)
- [ ] ADR created if the classification decision is non-obvious
