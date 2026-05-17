# Skill: Operations

**Domain**: sdlc
**Activation triggers**: Post-mortem, runbook, SLO, SLI, SRE, on-call, operations, incident management, error budget, on-call rotation, blameless post-mortem
**References**: specs/sdlc/04-definition-of-done.md, specs/observability/11-slo-definitions.md, ADR-0010, ADR-0015

---

## On-Call Responsibilities

| Responsibility                            | Action                                                             |
| ----------------------------------------- | ------------------------------------------------------------------ |
| Receive P1/P2 page from PagerDuty         | Acknowledge within 5 min (P1) or 15 min (P2)                       |
| Review Copilot severity classification    | Override at `POST /incidents/{id}/severity` if incorrect (HOTL)    |
| Review RCA hypothesis                     | Reject at `POST /incidents/{id}/rca/reject` with feedback if wrong |
| Approve remediation action                | Approve at `POST /incidents/{id}/remediation/approve` (HITL)       |
| Monitor Golden Signals during remediation | Watch Grafana dashboard; escalate if metrics don't recover         |
| Escalate if HITL window expires           | Page Engineering Lead; do not auto-execute                         |

---

## SLO Error Budget Policy (from spec 11)

| Budget remaining | Allowed actions                                                |
| ---------------- | -------------------------------------------------------------- |
| > 50%            | Normal velocity; deploy freely                                 |
| 25 – 50%         | Caution; deprioritise non-critical deploys; investigate trends |
| 10 – 25%         | Freeze non-critical feature deploys; focus on reliability work |
| 5 – 10%          | Freeze all feature deploys; mandatory reliability sprint       |
| 0 – 5%           | Incident response mode; no deploys without SRE Lead approval   |
| 0% (exhausted)   | All deploys frozen; automatic P1 opened; SRE Lead + Tech Lead  |

---

## Blameless Post-Mortem (ADR-0010)

**Trigger:** any P1 or P2 incident, or any incident where MTTR > target, or UNKNOWN_REMEDIATION.

**Deadline:** draft within 5 business days of incident close; published within 90 days.

### 8-Section Format (mandatory)

1. **Executive summary** — MTTD, MTTR, severity, business impact (CUJ affected)
2. **Timeline** — T₀ → T₄ from audit trail events (millisecond precision)
3. **Root cause** — RCAAgent hypothesis + human confirmation; confidence score
4. **Contributing factors** — list each; distinguish root from contributing
5. **Action items** — each item: owner role + due date + issue link
6. **What went well** — at least 2 items; recognize effective responses
7. **What can be improved** — tied to action items; no blame on individuals
8. **Appendix** — relevant metric graphs, log excerpts (PII scrubbed), trace IDs

**Privacy:** role labels only (`engineer_alpha`, `on_call_engineer`) — no real names (ADR-0010).

### PostMortemAgent output

The PostMortemAgent drafts the post-mortem from the audit trail (HOTL). The on-call engineer reviews before publishing. Engineer may add context not captured in the audit trail.

---

## Runbook Structure

Every agent capability and remediation action type must have a runbook entry in `docs/runbooks/`.

| Field               | Content                                                   |
| ------------------- | --------------------------------------------------------- |
| Title               | Short description of the scenario                         |
| Incident type       | availability / latency / error_rate / saturation          |
| Severity            | P1 / P2 / P3 / P4                                         |
| Autonomy            | HITL / HOTL / BLOCKED                                     |
| RTO target          | Time from detection to resolution target                  |
| Trigger condition   | Exact metric threshold from spec 11                       |
| Diagnosis steps     | Numbered; reference Grafana dashboard and Loki query      |
| Remediation options | Ranked by confidence; each with action type and HITL note |
| Rollback            | Undo procedure for each remediation option                |
| Escalation          | When and how to escalate to Engineering Lead              |

---

## SLI / SLO Quick Reference (spec 11)

| SLI    | Metric                              | SLO — Critical tier   | SLO — Standard tier |
| ------ | ----------------------------------- | --------------------- | ------------------- |
| SLI-01 | Detection latency (MTTD P1)         | < 5 min               | < 15 min            |
| SLI-02 | Triage latency                      | < 2 min               | < 5 min             |
| SLI-03 | RCA latency                         | < 10 min              | < 20 min            |
| SLI-04 | Remediation latency (post-approval) | < 15 min              | < 30 min            |
| SLI-05 | Audit trail write success rate      | 100% (zero tolerance) | 100%                |

Error budgets are consumed when SLOs are missed. Budget policy above governs deploy freeze.

---

## Escalation Matrix

| Condition                            | Escalation target | Action                                    |
| ------------------------------------ | ----------------- | ----------------------------------------- |
| HITL approval window expires         | Engineering Lead  | Page; severity bumped +1; no auto-execute |
| Two consecutive remediation failures | Engineering Lead  | Freeze automation; manual investigation   |
| RCAAgent confidence < 0.6            | On-call engineer  | Surface low-confidence label; manual RCA  |
| Audit trail write failure            | SRE Lead          | Kill-switch automatic; P1 opened          |
| Kill-switch re-activated within 60s  | Tech Lead         | Full stop; root cause review required     |
| P1 MTTR > 30 min                     | Engineering Lead  | Escalate; post-mortem mandatory           |

---

## Capacity Planning Signals

Monitor these to prevent saturation incidents:

| Signal                  | Prometheus metric                   | Alert threshold       |
| ----------------------- | ----------------------------------- | --------------------- |
| HITL queue depth        | `hitl_queue_depth`                  | > 5 pending approvals |
| LLM token budget used   | `llm_token_budget_used_ratio`       | > 0.8                 |
| Audit trail lag         | `audit_trail_write_lag_seconds`     | > 5s                  |
| Agent CPU saturation    | `container_cpu_usage_seconds_total` | > 80% for 5 min       |
| Vault lease expiry risk | `vault_lease_ttl_seconds`           | < 300s (5 min)        |
