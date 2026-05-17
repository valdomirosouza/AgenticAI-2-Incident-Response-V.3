# Skill: Incident Lifecycle

**Domain**: domain
**Activation triggers**: Incident lifecycle, incident response flow, post-mortem, runbook, RCA, remediation flow, SRE, on-call
**References**: specs/system/03-incident-lifecycle.md, ADR-0004, ADR-0010, ADR-0015

---

## Lifecycle Overview

```
  T₀           T₁              T₂          T₃              T₄           T₅
  │            │               │           │               │            │
  ▼            ▼               ▼           ▼               ▼            ▼
ONSET ──► DETECTION ──► TRIAGE ──► INVESTIGATION ──► REMEDIATION ──► CLOSED
           │                │              │               │
           │◄──── MTTD ────►│              │               │
           │                │◄─────────────────── MTTR ───►│
```

| Stage         | Start event             | End event               | Owner agent      | Autonomy |
| ------------- | ----------------------- | ----------------------- | ---------------- | -------- |
| Onset         | First anomalous signal  | —                       | —                | —        |
| Detection     | `incident.created`      | `incident.severity_set` | DetectionAgent   | HOTL     |
| Triage        | `incident.severity_set` | `rca.hypothesis_set`    | TriageAgent      | HOTL     |
| Investigation | `rca.hypothesis_set`    | `remediation.proposed`  | RCAAgent         | HOTL     |
| Remediation   | ApprovalToken granted   | `incident.resolved`     | RemediationAgent | **HITL** |
| Post-mortem   | `incident.resolved`     | `postmortem.drafted`    | PostMortemAgent  | HOTL     |

---

## Stage Detail

### Detection (T₀ → T₁)

**Trigger:** Golden Signal threshold breach detected by DetectionAgent scanning
Prometheus metrics at the configured burn rate (ADR-0015).

**Output:** `incident.created` audit event with:

- Incident ID (`inc-YYYY-MMDD-NNN`)
- Triggering metric and value
- Affected service
- Timestamp T₁ (used to compute MTTD)

**MTTD target:** < 5 min for P1, < 15 min for P2 (spec 11 SLO thresholds).

**Deduplication:** OrchestratorAgent suppresses duplicate `incident.created` events
within a 5-minute correlation window for the same service and metric.

---

### Triage (T₁ → T₂)

**Input:** `incident.created` event + current Golden Signal readings.

**Process:**

1. TriageAgent queries Prometheus for current error rate, latency p99, saturation.
2. Classifies severity P1–P4 using the threshold table (spec 11).
3. Identifies affected Critical User Journeys (CUJs).
4. Emits `incident.severity_set` with confidence score.
5. Pages on-call via PagerDuty/Slack (automated, HOTL).

**Severity classification:**

| Severity | Error rate / latency condition                | CUJ impact        | Notification   |
| -------- | --------------------------------------------- | ----------------- | -------------- |
| P1       | > 50% error rate OR complete outage           | All CUJs degraded | Immediate page |
| P2       | > 5% on Critical tier OR latency p99 > 2× SLO | One CUJ degraded  | Page in 5 min  |
| P3       | Non-critical service degraded                 | No CUJ impact     | Ticket + Slack |
| P4       | Informational anomaly                         | No impact         | Ticket only    |

**Override:** On-call engineer may override severity via `POST /incidents/{id}/severity`
within the triage window.

---

### Investigation / RCA (T₂ → T₃)

**Input:** `incident.severity_set` + relevant log/trace/metric excerpts.

**Process:**

1. RCAAgent queries Loki (logs) and Tempo (traces) for the incident time window.
2. Constructs a causal hypothesis from correlated anomalies.
3. Scores confidence (0.0–1.0); if < 0.6 → emits `rca.confidence_low` and surfaces
   low-confidence label to the on-call engineer.
4. Emits `rca.hypothesis_set` with hypothesis text and confidence.

**Prompt construction:** Log/trace excerpts are PII-sanitized (ADR-0028) before being
sent to the LLM. Only relevant excerpts are included — not full log dumps.

**Engineer interaction:** Engineer may reject the hypothesis (`POST /incidents/{id}/rca/reject`),
which triggers a new RCA pass with the engineer's feedback injected.

---

### Remediation (T₃ → T₄)

**Input:** `rca.hypothesis_set` + runbook content.

**Process:**

1. RemediationAgent matches RCA hypothesis to known runbook patterns.
2. Proposes one or more `PRODUCTION_*` actions ranked by confidence.
3. Emits `remediation.proposed` (HOTL — engineer reviews).
4. **HITL gate:** engineer approves via `POST /incidents/{id}/remediation/approve`.
   ApprovalToken (HMAC-SHA256, ADR-0023) is issued and validated by `action_executor`.
5. `action_executor` executes the approved action.
6. Monitors Golden Signals for recovery; emits `incident.resolved` when metrics
   return within SLO bounds.

**Timeout:** If no approval within the P-severity window (P1: 5 min, P2: 15 min,
P3: 60 min), the incident is escalated — **never auto-executed**.

**Unknown remediation:** If no runbook matches, the proposal is flagged
`UNKNOWN_REMEDIATION` and HITL is mandatory regardless of severity.

---

### Post-mortem (T₄ → T₅)

**Input:** Full audit trail for the incident.

**Process:**

1. PostMortemAgent reconstructs the incident timeline from audit events (ADR-0024).
2. Drafts a blameless post-mortem following the 8-section format (ADR-0010).
3. Emits `postmortem.drafted` — surfaced for human review (HOTL).
4. Engineer reviews and publishes within 90 days of incident close.

**Mandatory post-mortem sections (ADR-0010):**

1. Executive summary (MTTD, MTTR, severity, impact)
2. Timeline (T₀ → T₄ from audit trail)
3. Root cause (RCAAgent hypothesis, human-confirmed)
4. Contributing factors
5. Action items (owner roles + due dates)
6. What went well
7. What can be improved
8. Appendix (relevant metrics, log excerpts — PII scrubbed)

**Privacy:** Role labels only (e.g. `engineer_alpha`) — no real names (ADR-0010).
Post-mortem retained for 90 days post-close then archived (ADR-0030).

---

## Escalation Rules

| Condition                                 | Action                                                           |
| ----------------------------------------- | ---------------------------------------------------------------- |
| HITL approval window expires              | Escalate severity +1 level; page backup on-call; no auto-execute |
| RCAAgent confidence < 0.6                 | Surface low-confidence label; request human investigation        |
| No runbook match for proposed action      | Flag `UNKNOWN_REMEDIATION`; HITL mandatory                       |
| Two consecutive remediation failures      | Escalate to Engineering Lead; freeze automation                  |
| Duplicate `incident.created` within 5 min | Deduplicate; extend existing incident                            |

---

## Measurement Points for MTTD / MTTR

All timestamps sourced from the immutable audit trail (ADR-0024) — no manual entry.

| Metric           | Formula        | Audit event used                                             |
| ---------------- | -------------- | ------------------------------------------------------------ |
| MTTD             | T₁ − T₀        | `incident.created.timestamp` − first anomalous metric sample |
| Triage time      | T₂ − T₁        | `incident.severity_set` − `incident.created`                 |
| RCA time         | T₃ − T₂        | `remediation.proposed` − `rca.hypothesis_set`                |
| HITL wait        | T_approve − T₃ | `remediation.approved` − `remediation.proposed`              |
| Remediation time | T₄ − T_approve | `incident.resolved` − `remediation.approved`                 |
| MTTR             | T₄ − T₁        | `incident.resolved` − `incident.created`                     |

---

## Quick Reference: Quantitative Targets

| Stage            | P1 target | P2 target | P3/P4 target |
| ---------------- | --------- | --------- | ------------ |
| MTTD (Detection) | < 5 min   | < 15 min  | < 60 min     |
| Triage           | < 2 min   | < 5 min   | < 15 min     |
| Investigation    | < 10 min  | < 20 min  | < 60 min     |
| HITL window      | 5 min     | 15 min    | 60 min       |
| Remediation      | < 15 min  | < 30 min  | < 120 min    |
| Total MTTR       | < 30 min  | < 60 min  | < 180 min    |
