# Spec 17: Audit Trail

**Domain**: ethics
**Owner**: Tech Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #13
**Linked ADRs**: ADR-0024
**Review cadence**: Semi-annually; Ethics reviewer required

---

## 1. Purpose

Define the immutable decision log schema, tamper-evidence mechanism, retention rules,
access control and query interface for the Copilot audit trail.

---

## 2. Context

ADR-0024 established an append-only hash-chained audit trail as the authoritative record
of every agent decision. EU AI Act Art. 12 requires logging of high-risk AI system
operation. SOC 2 CC7 requires audit logging of system activity. This spec translates
the ADR into a precise schema contract and operational policy.

---

## 3. Decision

### 3.1 Audit event schema

Every audit event is a JSON document stored as an immutable object:

```json
{
  "record_id": "aud-2026-0517-001-00001",
  "incident_id": "inc-2026-0517-001",
  "event_type": "hitl.approval_requested",
  "agent_role": "remediation_agent",
  "action_type": "PRODUCTION_pod_restart",
  "payload": { "service": "orchestrator", "namespace": "copilot" },
  "confidence": 0.87,
  "timestamp": "2026-05-17T14:32:01.123Z",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "prev_hash": "sha256:e3b0c44298fc1c149afb...",
  "record_hash": "sha256:a665a45920422f9d417e..."
}
```

### 3.2 Field definitions

| Field         | Type     | Required | Description                                                                             |
| ------------- | -------- | -------- | --------------------------------------------------------------------------------------- |
| `record_id`   | string   | Yes      | `aud-<date>-<incident_id>-<seq>` — unique, sequential per incident                      |
| `incident_id` | string   | Yes      | Links record to incident; `SYSTEM` for non-incident events                              |
| `event_type`  | enum     | Yes      | Controlled vocabulary (§3.3) — no free-form strings                                     |
| `agent_role`  | string   | Yes      | Source agent: `orchestrator`, `detection`, `triage`, `rca`, `remediation`, `postmortem` |
| `action_type` | string   | No       | Set only for action events; matches HITL matrix (spec 16)                               |
| `payload`     | object   | Yes      | Event-specific data; PII-scrubbed (no raw user data)                                    |
| `confidence`  | float    | No       | Required for `rca.*` and `remediation.*` events; range 0.0–1.0                          |
| `timestamp`   | ISO 8601 | Yes      | UTC; millisecond precision; sourced from system clock                                   |
| `trace_id`    | string   | Yes      | W3C TraceContext `traceparent` trace_id — links to OTel spans                           |
| `span_id`     | string   | Yes      | W3C TraceContext span_id                                                                |
| `prev_hash`   | string   | Yes      | SHA-256 of previous record in the incident chain; `sha256:0000…` for first record       |
| `record_hash` | string   | Yes      | SHA-256(`record_id` + `event_type` + `timestamp` + `prev_hash` + `payload`)             |

### 3.3 Event type vocabulary

```
incident.created          incident.severity_set     incident.escalated
incident.resolved         incident.closed
rca.hypothesis_set        rca.confidence_low        rca.rejected
remediation.proposed      remediation.approved      remediation.rejected
remediation.executed      remediation.failed
hitl.approval_requested   hitl.approval_granted     hitl.approval_expired
hitl.validation_failed
pii.masked
audit.write_failed
postmortem.drafted        postmortem.published
agent.kill_switch_activated
audit.secret_rotated
```

Free-form event_type values are rejected by the `AuditEvent` Pydantic model at write
time. Any new event type requires a schema migration PR before use.

### 3.4 Hash chain integrity

Each incident has its own hash chain. The chain is:

```
Record 1: prev_hash = sha256(0000…0)  record_hash = sha256(R1_fields)
Record 2: prev_hash = record_hash(R1) record_hash = sha256(R2_fields + prev_hash)
Record 3: prev_hash = record_hash(R2) record_hash = sha256(R3_fields + prev_hash)
…
```

Chain validation algorithm:

```python
def validate_chain(records: list[AuditEvent]) -> bool:
    for i, record in enumerate(records):
        expected_prev = "sha256:" + "0" * 64 if i == 0 else records[i-1].record_hash
        if record.prev_hash != expected_prev:
            return False
        computed = sha256(record.record_id + record.event_type + record.timestamp
                         + record.prev_hash + json.dumps(record.payload, sort_keys=True))
        if record.record_hash != "sha256:" + computed:
            return False
    return True
```

Chain validation runs:

- On every read from the audit trail API.
- As a nightly scheduled job (raises P1 alert on any chain break).
- Before any DPIA/RIPD compliance evidence export.

### 3.5 Tamper-evidence mechanisms

| Layer              | Mechanism                                                                 |
| ------------------ | ------------------------------------------------------------------------- |
| **Storage**        | GCS object with Object Lock (WORM) — no DELETE or overwrite possible      |
| **Hash chain**     | SHA-256 prev_hash links — any gap or modification breaks the chain        |
| **Write endpoint** | Append-only; no PUT, PATCH or DELETE endpoints on `/audit/events`         |
| **Access control** | Write: `audit_adapter` service account only; Read: Tech Lead + audit jobs |
| **Nightly check**  | Automated chain integrity validation; P1 alert on any break               |

### 3.6 Access control

| Role                  | Read | Write | Delete |
| --------------------- | ---- | ----- | ------ |
| `audit_adapter` (svc) | Yes  | Yes   | **No** |
| Tech Lead             | Yes  | No    | **No** |
| SRE on-call           | Yes  | No    | **No** |
| CI/CD pipeline        | No   | No    | **No** |
| Any other             | No   | No    | **No** |

Deletion is architecturally impossible via the API (no DELETE endpoint). Direct GCS
object deletion requires the GCS admin role, which is not granted to any service account
in the Copilot deployment. Data subject erasure requests (LGPD art. 18) are handled by
replacing `user_id` values with `[DELETED]` in-place — the record structure and hash
chain are preserved (see ADR-0030).

### 3.7 Retention and archival

Per ADR-0030:

| Phase    | Duration      | Storage tier                  | Access               |
| -------- | ------------- | ----------------------------- | -------------------- |
| Active   | 0–6 months    | GCS Standard                  | Full query access    |
| Archive  | 6–24 months   | GCS Nearline                  | Query within 24h SLA |
| Deletion | After 2 years | Object lifecycle rule: delete | —                    |

Audit trail records are the only data category with a minimum retention (2 years); all
other categories have a maximum. The 2-year minimum is driven by SOC 2 CC7 and EU AI
Act Art. 12 obligations.

### 3.8 Query interface

The `AuditPort` exposes three read operations:

```python
def get_incident_trail(incident_id: str) -> list[AuditEvent]:
    """Returns all events for an incident, ordered by timestamp, chain validated."""

def get_events_by_type(event_type: str, since: datetime, until: datetime) -> list[AuditEvent]:
    """Returns events of a given type in a time window (for compliance reporting)."""

def validate_incident_chain(incident_id: str) -> ChainValidationResult:
    """Returns pass/fail + first broken link if chain is invalid."""
```

No raw GCS access is exposed — all reads go through `AuditPort` which enforces chain
validation before returning results.

### 3.9 Privacy Impact

- `payload` fields are scrubbed by the writing agent before submission — no raw PII
  (engineer names, user emails, IP addresses). Role labels only (e.g. `engineer_alpha`).
- `agent_role` is a functional role, not a person identifier.
- Data subject erasure (LGPD art. 18 / GDPR art. 17): `user_id` references in `payload`
  are replaced with `[DELETED]` in-place. The `record_hash` is recomputed and noted as
  `[REDACTED_FOR_ERASURE]` in a companion erasure-log record appended to the chain.
- Audit trail is not transferred to the Anthropic API or any external system.

---

## 4. Acceptance Criteria

- [ ] Audit event schema has all 12 fields with type, required flag and description
- [ ] Event type vocabulary contains all 22 event types
- [ ] Hash chain algorithm documented with Python pseudocode showing prev_hash linkage
- [ ] Tamper-evidence table covers storage (WORM), hash chain, endpoint design and nightly check
- [ ] Access control table: write limited to `audit_adapter`; no DELETE role exists
- [ ] Retention policy references ADR-0030 (2-year minimum, GCS Object Lock)
- [ ] Query interface defines 3 read operations with chain validation on every read
- [ ] Privacy Impact covers payload scrubbing, erasure procedure and no external transfer
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                            |
| -------- | -------------------------------------------------------------------- |
| ADR-0012 | OpenTelemetry — `trace_id`/`span_id` in every audit event            |
| ADR-0020 | Vault — `audit_adapter` GCS service account (S-03) from Vault        |
| ADR-0024 | Immutable audit trail — hash chain, append-only storage, event types |
| ADR-0030 | Data retention — 2-year minimum; GCS lifecycle rule for deletion     |

---

## References

- EU AI Act (2024) Art. 12 — Record-keeping for high-risk AI systems
- SOC 2 CC7 — System monitoring and audit logging
- LGPD Art. 18 — Data subject erasure rights
- GDPR Art. 17 — Right to erasure
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md`
- `specs/ethics/16-autonomy-boundaries.md` — action types that generate audit events
- `specs/observability/09-logging-schema.md` — `event` vocabulary shared with log events
