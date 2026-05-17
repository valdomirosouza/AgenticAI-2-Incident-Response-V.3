# ADR-0023: HITL Required for All Autonomous Remediation in Production

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Ethics Reviewer — researcher)
**Affected RQs**: RQ3 (autonomy and guardrails), RQ4 (compliance)

---

## Context

The RemediationAgent can propose and, if unconstrained, execute actions with direct
production impact: restarting services, rolling back deployments, scaling resources,
modifying load balancer rules, draining traffic from a node. A hallucinated or
miscalibrated remediation action can cause the same or worse outage than the incident
it was meant to resolve.

CLAUDE.md §1.6 Success Criterion 6 is a hard project gate: _"HITL controls are active
for all autonomous remediation actions in production."_ This is non-negotiable for the
dissertation to claim safe Agentic AI design.

Two regulatory frameworks independently mandate human oversight for high-risk AI actions:

- **EU AI Act Art. 14** (Human oversight measures): high-risk AI systems must allow
  human oversight and the ability to intervene, halt or override the system at any time.
- **NIST AI RMF GOVERN-5** (Organizational roles and responsibilities): clearly defined
  human oversight roles for AI systems with consequential outputs.

The HITL gate must be:

1. **Cryptographically enforced** — not just a policy; the RemediationAgent cannot
   execute any action without a valid, unexpired approval token signed by an
   authorised approver.
2. **Auditable** — every HITL decision (approve/reject/timeout) is recorded in the
   immutable audit trail (ADR-0024).
3. **Time-bounded** — an approval request cannot block indefinitely; a timeout
   triggers escalation, not silent execution.
4. **Role-constrained** — the approver must hold the `incident-commander` or
   `on-call-lead` role; the agent cannot approve its own actions.

## Decision

**No remediation action executes in production without an explicit, cryptographically
valid human approval token.** This is an absolute constraint — there are no
exceptions, overrides or degraded-mode bypasses.

### HITL trigger conditions

A HITL approval request is generated whenever the RemediationAgent proposes any action
in the `ActionType.PRODUCTION_*` namespace:

| Action type           | Example                                              | HITL required        |
| --------------------- | ---------------------------------------------------- | -------------------- |
| `PRODUCTION_RESTART`  | Restart a Kubernetes pod or service                  | Yes — always         |
| `PRODUCTION_ROLLBACK` | Roll back a deployment to previous version           | Yes — always         |
| `PRODUCTION_SCALE`    | Change replica count or resource limits              | Yes — always         |
| `PRODUCTION_TRAFFIC`  | Modify load balancer weights or drain node           | Yes — always         |
| `PRODUCTION_CONFIG`   | Change runtime configuration (feature flag, env var) | Yes — always         |
| `STAGING_*`           | Any action in staging environment                    | No — HOTL monitoring |
| `NOTIFY_*`            | Page on-call, post to Slack, create ticket           | No — HOTL monitoring |
| `QUERY_*`             | Read-only queries (logs, metrics, traces)            | No                   |

### Approval token specification

```
ApprovalToken {
  incident_id:    string        // incident being remediated
  action_id:      uuid          // unique ID of the proposed action
  action_type:    ActionType    // must be PRODUCTION_*
  action_payload: bytes         // serialised, signed action parameters
  approver_id:    string        // opaque role-based ID (not personal name)
  approver_role:  enum          // incident-commander | on-call-lead
  issued_at:      ISO8601 UTC
  expires_at:     ISO8601 UTC   // issued_at + timeout_sla
  signature:      bytes         // HMAC-SHA256 over (action_id + action_payload + expires_at)
                                //   using HITL signing key (stored in Vault, ADR-0020)
}
```

### Approval timeout SLA

| Incident severity | Approval timeout | On timeout                                                     |
| ----------------- | ---------------- | -------------------------------------------------------------- |
| P1                | 5 minutes        | Escalate to incident commander + secondary on-call; page again |
| P2                | 15 minutes       | Escalate to on-call lead; create ticket                        |
| P3                | 60 minutes       | Create ticket; no escalation                                   |

**On timeout the action is NOT executed.** Escalation is triggered but the
RemediationAgent does not self-approve or fall back to autonomous execution.
This is the critical distinction from a "soft HITL" — there is no timeout-based
auto-execute fallback.

### Enforcement mechanism

The `action_executor` in `src/guardrails/action_executor.py` validates the
approval token before every `PRODUCTION_*` action:

```python
def execute(action: ProductionAction, token: ApprovalToken) -> ActionResult:
    validate_token_signature(token, vault.get("hitl/signing_key"))
    validate_token_not_expired(token)
    validate_token_matches_action(token, action)
    validate_approver_role(token)
    # Only reaches here if all validations pass
    return adapter.execute(action)
```

If any validation fails, `HitlValidationError` is raised and the action is logged
as `BLOCKED` in the audit trail (ADR-0024). The exception is never silently swallowed.

### HITL approval UI

The approval interface is the human-facing component of the HITL gate. It must display:

- The proposed action in plain language (not raw JSON)
- The incident context: current severity, affected services, MTTD so far
- The RCA hypothesis that motivated the action
- The confidence score of the RCAAgent
- The action's estimated blast radius
- An explicit `[APPROVE]` and `[REJECT]` button with confirmation prompt

The UI must label all agent-generated content with `AI-GENERATED` (OWASP LLM09
mitigation — ADR-0021) to prevent overreliance.

## Alternatives Considered

| Alternative                                    | Pros                                                                        | Cons                                                                                                                      |
| ---------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **No HITL (full autonomy)**                    | Fastest MTTR                                                                | EU AI Act Art. 14 violated; catastrophic blast radius on hallucination; CLAUDE.md §1.6 criterion 6 not met                |
| **HITL with auto-execute fallback on timeout** | Avoids blocked incidents                                                    | Timeout bypass negates the HITL guarantee; an attacker can induce timeout to execute malicious actions                    |
| **HITL for P1 only**                           | Reduced friction for P2/P3                                                  | Inconsistent autonomy model; P2 incidents can also affect production with equal blast radius                              |
| **HITL for all PRODUCTION\_\* actions** ✅     | Consistent model; cryptographic enforcement; no bypass; EU AI Act compliant | Adds approval latency to MTTR — accepted trade-off; MTTD is the primary metric (ADR-0015 fires faster than HITL approval) |

## Consequences

**Positive:**

- CLAUDE.md §1.6 criterion 6 satisfied: HITL controls active for all production
  remediation — no autonomous production execution ever.
- EU AI Act Art. 14: human oversight and intervention capability guaranteed by
  cryptographic token; cannot be bypassed by code or configuration.
- Every HITL decision is auditable: approver role, action, timestamp, token signature
  all recorded in the immutable audit trail (ADR-0024).
- NIST AI RMF GOVERN-5: human oversight roles (incident commander, on-call lead)
  explicitly defined and enforceable.

**Negative / Trade-offs:**

- HITL approval adds latency to MTTR. Accepted: the dissertation hypothesis is that
  MTTD improvement (automated detection + triage) delivers more MTTR benefit than
  the approval latency costs. Measured quantitatively in the evaluation.
- P1 5-minute timeout may feel short for complex incidents — the timeout triggers
  escalation, not execution, so the risk is a delayed response, not an unsafe action.

## Review Criteria

Revisit this decision if:

- Evaluation experiments show that HITL approval latency dominates MTTR to the
  point where the Copilot delivers no net MTTR improvement — consider a pre-approved
  action allow-list for specific low-blast-radius P1 actions (requires a new ADR).
- EU AI Act implementing acts clarify that a specific category of AI system may
  operate without HITL in production — evaluate applicability and create a new ADR.

## References

- EU AI Act (2024) Art. 14 — Human oversight measures
- NIST AI RMF (2023) GOVERN-5 — Organizational roles, responsibilities and authorities
- OWASP LLM Top 10 (2025) LLM09 — Misinformation / Overreliance
- `docs/adr/ADR-0004-multi-agent-orchestration-pattern.md` — HITL gate in Orchestrator
- `docs/adr/ADR-0020-zero-trust-secrets-management.md` — HITL signing key in Vault
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md` — audit trail for HITL decisions
- `specs/ethics/16-autonomy-boundaries.md` — autonomy boundary spec (to be authored, issue #13)
- CLAUDE.md §1.3 — Autonomy model; §1.6 criterion 6 — HITL hard gate
