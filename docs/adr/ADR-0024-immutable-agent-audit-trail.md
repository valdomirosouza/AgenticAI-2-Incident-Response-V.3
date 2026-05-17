# ADR-0024: Immutable Audit Trail for Every Agent Decision

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Ethics Reviewer — researcher)
**Affected RQs**: RQ3 (guardrails and accountability), RQ4 (compliance)

---

## Context

An Agentic AI system that acts in production must be accountable: every decision,
every action proposal, every HITL approval and every guardrail trigger must be
reconstructible after the fact. This is required by three independent frameworks:

1. **SOC 2 CC7** (System monitoring): service organisations must monitor systems
   to detect and respond to security events. An audit trail is the primary evidence
   of monitoring.
2. **ISO 27001 A.12.4** (Logging and monitoring): event logs must be protected
   against tampering and unauthorised access.
3. **EU AI Act Art. 12** (Record-keeping): providers of high-risk AI systems must
   keep logs of operation "to the extent such logs are under their control" —
   sufficient to assess compliance with requirements over time.

The audit trail is also the primary data source for:

- The PostMortemAgent: incident timeline reconstruction (ADR-0010).
- The dissertation evaluation: evidence that HITL was active, guardrails triggered
  as expected, and agent decisions were correct (CLAUDE.md §1.6 criterion 6).
- Legal/regulatory inquiry: if a remediation action causes damage, the audit trail
  must establish who approved what and when.

**Immutability requirement:** the audit trail must be tamper-evident. An attacker
or a misconfigured agent must not be able to delete or modify audit records to cover
their tracks. ISO 27001 A.12.4 explicitly requires protection against modification.

## Decision

Every agent decision event is written as an **append-only, cryptographically chained**
audit record. No audit record can be modified or deleted after creation.

### Audit event taxonomy

| Event type                 | Emitted by        | When                                    |
| -------------------------- | ----------------- | --------------------------------------- |
| `incident.created`         | OrchestratorAgent | New incident detected                   |
| `incident.state_changed`   | OrchestratorAgent | State machine transition                |
| `agent.invoked`            | OrchestratorAgent | Specialist agent started                |
| `agent.completed`          | Specialist agent  | Specialist agent returned result        |
| `triage.severity_assigned` | TriageAgent       | Severity score produced                 |
| `rca.hypothesis_generated` | RCAAgent          | RCA hypothesis with confidence score    |
| `remediation.proposed`     | RemediationAgent  | Action proposed, HITL requested         |
| `hitl.approval_requested`  | OrchestratorAgent | Approval token sent to human            |
| `hitl.approved`            | HITL UI           | Human approved action                   |
| `hitl.rejected`            | HITL UI           | Human rejected action                   |
| `hitl.timeout`             | OrchestratorAgent | Approval not received within SLA        |
| `guardrail.triggered`      | Any guardrail     | Guardrail blocked or modified an action |
| `action.executed`          | action_executor   | Production action executed              |
| `action.failed`            | action_executor   | Production action failed                |
| `postmortem.drafted`       | PostMortemAgent   | Post-mortem draft created               |

### Audit record schema

```json
{
  "event_id":     "uuid-v7",
  "event_type":   "hitl.approved",
  "incident_id":  "INC-2026-0042",
  "trace_id":     "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id":      "00f067aa0ba902b7",
  "agent":        "orchestrator",
  "timestamp":    "2026-05-17T14:23:01.456789Z",
  "payload":      { ... },
  "prev_hash":    "sha256:a1b2c3...",
  "record_hash":  "sha256:d4e5f6..."
}
```

`prev_hash` is the SHA-256 of the previous audit record for the same `incident_id`.
`record_hash` is SHA-256 of the current record including `prev_hash` — forming a
hash chain. Any modification to a historical record breaks all subsequent hashes,
making tampering detectable.

### Immutability enforcement

**Storage:** audit records are written to an **append-only log store**:

| Environment | Storage backend                                             | Immutability mechanism                                              |
| ----------- | ----------------------------------------------------------- | ------------------------------------------------------------------- |
| Development | Local append-only file + SQLite (WAL mode, no DELETE)       | Application-enforced; no DELETE endpoint exposed                    |
| Production  | Cloud append-only storage (GCS object versioning / S3 WORM) | Bucket-level object lock — records cannot be overwritten or deleted |

**API:** the audit log service exposes only `POST /audit` (write) and `GET /audit/:incident_id` (read). No `PUT`, `PATCH` or `DELETE` endpoints exist. Enforced at the API layer and verified by SAST (Semgrep custom rule: detect DELETE handlers in audit service).

**Hash chain verification:** a `verify_chain(incident_id)` function reconstructs
the hash chain and confirms integrity. Run as part of the release gate and available
as an operational tool.

### PII in audit records

Audit records must not contain raw PII. The `payload` field is PII-masked by the
`PiiSanitizer` before writing (ADR-0014). `approver_id` in HITL records is a
pseudonymised role-based identifier — never a real name (ADR-0023).

### Retention

Audit trail records are retained for a minimum of **2 years** (ADR-0030 data
retention policy), aligned with SOC 2 and EU AI Act Art. 12 evidence requirements.

## Alternatives Considered

| Alternative                            | Pros                                                                                               | Cons                                                                                    |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Standard mutable database**          | Simple; easy to query                                                                              | Any admin can modify records; ISO 27001 A.12.4 tamper-evidence requirement not met      |
| **Log files only**                     | Zero infrastructure overhead                                                                       | Not queryable; no hash chain; easily deleted or rotated away                            |
| **Blockchain**                         | Theoretically immutable                                                                            | Massive complexity overhead; not needed for a controlled-environment research prototype |
| **Append-only log with hash chain** ✅ | Tamper-evident without blockchain; queryable; straightforward to implement; meets ISO 27001 A.12.4 | Hash chain verification adds ~5ms per write; negligible                                 |

## Consequences

**Positive:**

- EU AI Act Art. 12: complete, tamper-evident record of all agent operations
  available for regulatory inspection.
- SOC 2 CC7: system monitoring evidence is auditable — every agent decision and
  every HITL approval is in the audit trail.
- PostMortemAgent uses the audit trail as the primary data source for incident
  timeline reconstruction — no manual timeline reconstruction needed.
- Dissertation evaluation: the audit trail provides the exact sequence of agent
  decisions and HITL interactions used as evidence in the evaluation chapter.

**Negative / Trade-offs:**

- Hash chain adds write latency (~5ms) and a verification step for chain reads.
  Acceptable given audit writes are not on the critical MTTD path.
- Append-only storage with object lock in production requires careful IAM setup —
  even admins must not be able to delete records. Documented in the secrets
  management runbook (ADR-0020).

## Review Criteria

Revisit this decision if:

- The audit trail volume grows beyond 1GB/month — evaluate columnar storage
  (Parquet/BigQuery) instead of append-only file/SQLite for the production backend.
- EU AI Act implementing acts specify a mandatory audit log format that differs
  from the schema defined here — migrate the schema and update this ADR.

## References

- SOC 2 Type II CC7 — System monitoring
- ISO/IEC 27001:2022 A.12.4 — Logging and monitoring
- EU AI Act (2024) Art. 12 — Record-keeping requirements
- `docs/adr/ADR-0010-blameless-post-mortem-format.md` — PostMortemAgent uses audit trail
- `docs/adr/ADR-0013-structured-json-logging-schema.md` — log schema (audit extends this)
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md` — PII masking before audit write
- `docs/adr/ADR-0023-hitl-autonomous-remediation.md` — HITL events in audit trail
- `specs/ethics/17-audit-trail.md` — audit trail spec (to be authored, issue #13)
