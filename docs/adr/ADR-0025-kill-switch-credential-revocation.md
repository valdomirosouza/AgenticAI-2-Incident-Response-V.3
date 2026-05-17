# ADR-0025: Kill-Switch and Credential Revocation for Compromised Agents

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Ethics Reviewer — researcher)
**Affected RQs**: RQ3 (guardrails), RQ4 (security, compliance)

---

## Context

An Agentic AI system that can propose and (with human approval) execute production
actions represents a high-value target for compromise. A compromised agent could:

- Generate fraudulent HITL approval requests at scale.
- Exfiltrate observability data containing PII or secrets.
- Propose malicious remediation actions designed to cause an outage or pivot.
- Exhaust the error budget by generating false P1 incidents.

Two regulatory frameworks mandate the ability to halt or revoke a compromised AI system:

- **NIST AI RMF MANAGE-4** (AI risk treatments): organisations must be able to
  decommission, adjust or shut down an AI system when risks materialise.
- **ISO 27001 A.16** (Information security incident management): organisations must
  respond to security incidents including containment of compromised systems.

The kill-switch must be:

1. **Operable in < 60 seconds** from detection to agent cessation — before a compromised
   agent can complete a second round of actions.
2. **Independent of the compromised agent** — the kill-switch mechanism must not rely
   on the agent's own code path; a compromised agent might suppress its own shutdown.
3. **Credential-revocation complete** — halting the process is insufficient if the
   agent's credentials (Vault AppRole, API keys) remain valid; they must be revoked
   simultaneously to prevent re-use.
4. **Auditable** — the kill-switch activation and credential revocation are high-severity
   security events; they must be recorded in the audit trail (ADR-0024) and trigger
   incident notification.

## Decision

The system implements a **two-path kill-switch** that operates independently of the
agent process and revokes credentials atomically:

### Path 1 — Process termination (RTO: < 10 seconds)

Each agent service is deployed as a Kubernetes `Deployment`. The kill-switch sends
a `kubectl delete pod -l agent=<name>` command (or equivalent cloud API call) to
the Kubernetes control plane. The Kubernetes scheduler terminates the pod
immediately (`terminationGracePeriodSeconds: 0` for kill-switch invocations).

The kill-switch command is available via:

- **CLI:** `scripts/kill-agent.sh <agent-name>` (requires `incident-commander` kubeconfig)
- **OrchestratorAgent emergency stop:** `POST /orchestrator/emergency-stop` with
  a signed emergency token (separate from HITL tokens — see credential structure below)
- **GitHub Actions manual workflow:** `workflow_dispatch` trigger on `.github/workflows/kill-agent.yml`

### Path 2 — Credential revocation (RTO: < 30 seconds, concurrent with Path 1)

Immediately after pod termination, the following revocations are executed in parallel:

| Credential                | Revocation action                                                    | Tool          |
| ------------------------- | -------------------------------------------------------------------- | ------------- |
| Vault AppRole `secret_id` | `vault write auth/approle/role/<agent>/secret-id-accessor/destroy`   | Vault CLI     |
| LLM API key               | Anthropic API key rotation via `anthropic.api_keys.rotate(<key_id>)` | Anthropic SDK |
| mTLS certificate          | Revoke via Vault PKI: `vault write pki/revoke serial_number=<sn>`    | Vault CLI     |
| HITL signing key          | Rotate signing key in Vault; invalidates all pending approval tokens | Vault CLI     |

HITL signing key rotation invalidates all in-flight approval tokens immediately —
any pending HITL approval request from the compromised agent cannot be approved
after the kill-switch fires.

### Full kill-switch protocol

```
STEP 1 — Detect / Declare compromise
  Who:  incident commander or automated anomaly detector
  How:  observe anomalous agent behaviour OR receive security alert
  SLA:  < 60 seconds from detection to activation

STEP 2 — Activate kill-switch (< 10 seconds)
  Execute: scripts/kill-agent.sh <agent-name>
  Effect:  pod terminated; agent process stops

STEP 3 — Revoke credentials (< 30 seconds, concurrent with Step 2)
  Execute: scripts/revoke-credentials.sh <agent-name>
  Effect:  Vault AppRole, LLM API key, mTLS cert, HITL signing key all revoked

STEP 4 — Audit and notify (< 2 minutes)
  Write kill-switch event to immutable audit trail (ADR-0024):
    event_type: agent.kill_switch_activated
    agent: <name>
    activated_by: <role>
    credentials_revoked: [list]
  Notify: page incident commander, post to #incidents Slack channel

STEP 5 — Investigate
  Review audit trail for all actions taken by the compromised agent
  Assess blast radius: were any PRODUCTION_* actions proposed or approved?
  Conduct post-mortem (ADR-0010)

STEP 6 — Recovery
  Deploy clean agent from a known-good image (pinned digest, ADR-0022)
  Issue new credentials via Vault
  Resume incident response with human-only triage until agent is re-validated
```

### Kill-switch access control

| Role                 | Permission                                         |
| -------------------- | -------------------------------------------------- |
| `incident-commander` | Full kill-switch activation (all agents)           |
| `on-call-lead`       | Kill-switch activation for assigned agent only     |
| `security-lead`      | Full kill-switch + credential revocation audit     |
| Agent processes      | No self-kill permission (enforced by Vault policy) |

## Alternatives Considered

| Alternative                                          | Pros                                                                             | Cons                                                                              |
| ---------------------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Manual process only (document + contact ops)**     | Zero engineering cost                                                            | RTO > 5 minutes; no credential revocation; human-dependent under stress           |
| **Agent self-shutdown endpoint**                     | Simple                                                                           | Compromised agent can suppress its own shutdown                                   |
| **Two-path kill-switch (k8s + Vault revocation)** ✅ | Independent of agent code path; credentials revoked atomically; RTO < 60 seconds | Requires Vault and k8s access from kill-switch scripts; more complex to implement |
| **Container image signing + automatic quarantine**   | Proactive detection                                                              | High complexity; false positive risk; does not revoke credentials                 |

## Consequences

**Positive:**

- NIST AI RMF MANAGE-4 satisfied: documented, tested kill-switch with RTO < 60 seconds.
- ISO 27001 A.16 satisfied: compromised agent containment procedure is written,
  automated and auditable.
- HITL signing key rotation invalidates all in-flight fraudulent approval requests —
  no approved action can execute after the kill-switch fires.
- Kill-switch protocol is tested in staging via a scheduled drill (quarterly, per
  the ethics audit cadence — ADR-0026).

**Negative / Trade-offs:**

- Credential revocation requires Vault and cloud API access from the kill-switch
  scripts — these scripts must themselves be secured (access only to
  `incident-commander` role, stored in a restricted directory, not in the agent
  image).
- Kill-switch drill disrupts the staging environment for ~15 minutes per quarter —
  scheduled during low-activity periods.

## Review Criteria

Revisit this decision if:

- RTO target (< 60 seconds) is not achievable in the evaluation environment —
  diagnose and reduce latency in the kill-switch scripts.
- A new credential type is introduced (e.g. database password with long-lived session)
  that is not covered by the revocation steps — add it to the protocol.

## References

- NIST AI RMF (2023) MANAGE-4 — AI risk treatments: decommission and adjust
- ISO/IEC 27001:2022 A.16 — Information security incident management
- `docs/adr/ADR-0020-zero-trust-secrets-management.md` — Vault credential management
- `docs/adr/ADR-0023-hitl-autonomous-remediation.md` — HITL signing key revocation
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md` — kill-switch event logging
- `docs/adr/ADR-0026-algorithmic-bias-audit-cadence.md` — quarterly kill-switch drill
- `specs/ethics/16-autonomy-boundaries.md` — autonomy boundary spec (to be authored, issue #13)
