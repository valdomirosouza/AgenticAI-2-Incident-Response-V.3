# Spec 09: Logging Schema

**Domain**: observability
**Owner**: SRE Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #11
**Linked ADRs**: ADR-0013, ADR-0014
**Review cadence**: Quarterly or on schema change

---

## 1. Purpose

Define the mandatory JSON log schema, per-field PII masking rules, log level
conventions, retention policy per environment and the Loki label set that enables
efficient querying.

---

## 2. Context

ADR-0013 established the 11 mandatory fields and structured JSON format. ADR-0014
established PII masking at the OTel SpanProcessor layer before log ingestion.
CLAUDE.md §1.6 criterion 5 is a hard gate: observability pipelines must enforce PII
masking before ingestion into any third-party system. This spec operationalises both
ADRs into a field-by-field contract.

---

## 3. Decision

### 3.1 Mandatory log schema

Every log line emitted by any service or agent must be valid JSON containing all 11
mandatory fields:

```json
{
  "timestamp": "2026-05-17T14:32:01.123Z",
  "level": "INFO",
  "service": "orchestrator-agent",
  "version": "0.4.0",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "incident_id": "inc-2026-0517-001",
  "message": "Triage severity classified as P2",
  "event": "incident.severity_set",
  "duration_ms": 42,
  "user_id": "usr_a3f9b2"
}
```

### 3.2 Field definitions and PII rules

| Field         | Type     | Required | PII risk | Masking rule (ADR-0014)                                      |
| ------------- | -------- | -------- | -------- | ------------------------------------------------------------ |
| `timestamp`   | ISO 8601 | Yes      | None     | No masking required                                          |
| `level`       | enum     | Yes      | None     | No masking required                                          |
| `service`     | string   | Yes      | None     | No masking required                                          |
| `version`     | SemVer   | Yes      | None     | No masking required                                          |
| `trace_id`    | W3C hex  | Yes      | None     | No masking required                                          |
| `span_id`     | W3C hex  | Yes      | None     | No masking required                                          |
| `incident_id` | string   | Yes      | None     | No masking required                                          |
| `message`     | string   | Yes      | **High** | Presidio scan before emit; redact any detected PII entity    |
| `event`       | string   | Yes      | None     | Controlled vocabulary (see §3.4); no free-form PII           |
| `duration_ms` | integer  | Yes      | None     | No masking required                                          |
| `user_id`     | string   | Yes      | **High** | Replace real ID with pseudonymised opaque token `usr_<hash>` |

**Additional optional fields** (masked if present):

| Field          | PII risk | Masking rule                                     |
| -------------- | -------- | ------------------------------------------------ |
| `ip_address`   | High     | Replace with subnet: `10.x.x.0/24`               |
| `email`        | High     | Replace with `[MASKED_EMAIL]`                    |
| `request_path` | Medium   | Strip query parameters containing known PII keys |
| `stack_trace`  | Medium   | Presidio scan; redact before logging             |
| `error_detail` | Medium   | Presidio scan; redact before logging             |

No field may contain raw CPF, CNPJ, credit card numbers, passwords or session tokens.
The OTel SpanProcessor (ADR-0014) enforces this at the application layer; the Loki
Collector pipeline processor applies a defence-in-depth pass on ingestion.

### 3.3 Log levels

| Level   | When to use                                                                     |
| ------- | ------------------------------------------------------------------------------- |
| `DEBUG` | Detailed internal state for development; **never emitted in production**        |
| `INFO`  | Normal lifecycle events: agent invoked, decision taken, action proposed         |
| `WARN`  | Degraded but non-failing state: LLM confidence below threshold, retry scheduled |
| `ERROR` | Recoverable failure: LLM timeout, schema validation error, HITL window expired  |
| `FATAL` | Unrecoverable failure: audit trail write failure, kill-switch activated         |

`DEBUG` is gated by `LOG_LEVEL` env var; default in all environments is `INFO`.

### 3.4 Event vocabulary (`event` field)

The `event` field uses the same controlled vocabulary as the audit trail (ADR-0024):

```
incident.created         incident.severity_set    incident.escalated
incident.resolved        incident.closed
rca.hypothesis_set       rca.confidence_low
remediation.proposed     remediation.approved     remediation.rejected
remediation.executed     remediation.failed
hitl.approval_requested  hitl.approval_granted    hitl.approval_expired
pii.masked               audit.write_failed
postmortem.drafted
agent.kill_switch_activated
```

Free-form event strings are rejected by the log schema validator in the harness.

### 3.5 Loki label set

Loki labels are indexed and must be low-cardinality. Log line content (including all
mandatory fields above) is stored as unstructured text — only labels are indexed.

| Loki label | Value source       | Cardinality          |
| ---------- | ------------------ | -------------------- |
| `service`  | `service` field    | ~10                  |
| `level`    | `level` field      | 5                    |
| `env`      | deployment env var | 3 (dev/staging/prod) |

`trace_id`, `incident_id` and `user_id` are **not** Loki labels — they are queried
with `|= "trace_id=<value>"` log-line filtering, not label selectors, to avoid
cardinality explosion.

### 3.6 Retention policy per environment

Per ADR-0030:

| Environment | Hot retention | Cold archive | Backend config                  |
| ----------- | ------------- | ------------ | ------------------------------- |
| Production  | 30 days       | +60 days     | `retention_period: 90d` in Loki |
| Staging     | 7 days        | —            | `retention_period: 7d`          |
| Development | 1 day         | —            | `retention_period: 1d`          |

Logs containing pseudonymised `user_id` values are subject to data subject erasure
requests within 15 days (ADR-0030, LGPD art. 18).

### 3.7 Privacy Impact

- `message` and optional free-text fields are scanned by Presidio before emission
  (ADR-0014 OTel SpanProcessor).
- `user_id` is pseudonymised at source — the mapping table is stored in Vault
  (ADR-0020), never in the log pipeline.
- Log data is never forwarded to the Anthropic API — only sanitized prompt excerpts
  are (ADR-0028).
- Loki ingestion pipeline applies a defence-in-depth PII regex pass (ADR-0014).

---

## 4. Acceptance Criteria

- [ ] All 11 mandatory fields listed with type, required flag, PII risk and masking rule
- [ ] Optional high-risk fields (ip_address, email, stack_trace) have explicit masking rules
- [ ] Log level table covers all 5 levels with `DEBUG` gated from production
- [ ] `event` field has controlled vocabulary of at least 20 event types
- [ ] Loki label set is defined with cardinality guidance; high-cardinality fields excluded from labels
- [ ] Retention policy per environment references ADR-0030 TTL values
- [ ] Privacy Impact section documents Presidio scan, pseudonymised user_id and Loki defence-in-depth
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                           |
| -------- | ------------------------------------------------------------------- |
| ADR-0013 | Structured JSON logging — 11 mandatory fields, schema contract      |
| ADR-0014 | PII masking in observability — OTel SpanProcessor + Loki processor  |
| ADR-0020 | Vault — `user_id` pseudonymisation mapping stored in Vault          |
| ADR-0024 | Immutable audit trail — `event` vocabulary shared with audit events |
| ADR-0028 | PII sanitization — logs never forwarded to LLM API raw              |
| ADR-0030 | Data retention TTL — Loki `retention_period` per environment        |

---

## References

- CLAUDE.md §1.6 criterion 5 (PII masking before ingestion — hard gate)
- `docs/adr/ADR-0013-structured-json-logging-schema.md`
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md`
- `specs/observability/10-tracing-schema.md` — `trace_id`/`span_id` format
- `specs/privacy/19-pii-inventory.md` — full PII category inventory
