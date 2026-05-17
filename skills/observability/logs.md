# Skill: Logs

**Domain**: observability
**Activation triggers**: Structured logging, log levels, log schema, JSON logging, log fields, Loki, log retention, PII in logs, log masking, audit log
**References**: specs/observability/09-logging-schema.md, ADR-0013, ADR-0014

---

## Structured JSON Log Schema

Every log line is a single JSON object. The 11 mandatory fields must be present on every record.

### Mandatory fields

| Field         | Type     | Description                                      | PII risk | Masking rule                       |
| ------------- | -------- | ------------------------------------------------ | -------- | ---------------------------------- |
| `timestamp`   | ISO-8601 | UTC timestamp with millisecond precision         | No       | None                               |
| `level`       | string   | Log level (see §Log Levels)                      | No       | None                               |
| `service`     | string   | Service name (`src/` directory name)             | No       | None                               |
| `trace_id`    | string   | W3C TraceContext `traceparent` trace ID          | No       | None                               |
| `span_id`     | string   | W3C TraceContext `traceparent` span ID           | No       | None                               |
| `incident_id` | string   | Active incident ID (`inc-YYYY-MMDD-NNN`) or null | No       | None                               |
| `event_type`  | string   | Controlled vocabulary event (see §Event Types)   | No       | None                               |
| `agent`       | string   | Agent name or `null` if non-agent context        | No       | None                               |
| `action_type` | string   | Action type or `null`                            | No       | None                               |
| `message`     | string   | Human-readable description                       | **High** | Must not contain raw PII           |
| `payload`     | object   | Structured data for the event                    | **High** | PII fields replaced before logging |

### Mandatory field example

```json
{
  "timestamp": "2026-05-17T14:23:01.452Z",
  "level": "INFO",
  "service": "triage-agent",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "incident_id": "inc-2026-0517-003",
  "event_type": "incident.severity_set",
  "agent": "TriageAgent",
  "action_type": null,
  "message": "Severity classified as P1 (confidence 0.94)",
  "payload": {
    "severity": "P1",
    "confidence": 0.94,
    "error_rate": 0.67,
    "affected_service": "svc_payment_1"
  }
}
```

---

## Log Levels

| Level   | When to use                                           | Production enabled               |
| ------- | ----------------------------------------------------- | -------------------------------- |
| `ERROR` | Unhandled exception; action failed with no retry path | Yes                              |
| `WARN`  | Degraded path taken; retry succeeded; confidence low  | Yes                              |
| `INFO`  | Normal lifecycle events; state transitions            | Yes                              |
| `DEBUG` | Detailed internal state for troubleshooting           | **No** — gated out in production |
| `TRACE` | Per-call LLM prompt/response snippets (sanitized)     | **No** — never in production     |

`DEBUG` and `TRACE` are only enabled via feature flag in local/staging with explicit opt-in.

---

## PII Masking Rules (ADR-0014)

All PII must be masked **before** the log call — never in a post-processing step.

| PII category     | Masking rule                             | Example before → after                                       |
| ---------------- | ---------------------------------------- | ------------------------------------------------------------ |
| User ID / email  | Replace with role label                  | `user@example.com` → `engineer_alpha`                        |
| IP address       | Replace with subnet (`/24`)              | `192.168.1.42` → `192.168.1.0/24`                            |
| CPF / CNPJ       | Replace with `[REDACTED_CPF]`            | `123.456.789-00` → `[REDACTED_CPF]`                          |
| Hostname         | Replace with service category label      | `db-prod-03.internal` → `[REDACTED_HOST]`                    |
| Free-text fields | Run Presidio before including in payload | LLM prompt excerpts sanitized via `pii_sanitizer.sanitize()` |

```python
# Correct — PII masked before log call
logger.info(
    "Incident created",
    extra={
        "event_type": "incident.created",
        "payload": {
            "triggered_by": "engineer_alpha",       # role label, not real name
            "service": f"svc_{category}_{index}",  # generalised service name
        }
    }
)

# WRONG — raw PII in log
logger.info(f"Incident created by {user.email}")   # Semgrep G09 catches this
```

---

## Event Type Vocabulary (controlled — 22 types)

Use only these values for `event_type`. Adding a new type requires a spec update.

| Category    | Event types                                                                                  |
| ----------- | -------------------------------------------------------------------------------------------- |
| Incident    | `incident.created`, `incident.severity_set`, `incident.resolved`, `incident.escalated`       |
| RCA         | `rca.hypothesis_set`, `rca.confidence_low`, `rca.rejected`                                   |
| Remediation | `remediation.proposed`, `remediation.approved`, `remediation.executed`, `remediation.failed` |
| HITL        | `hitl.token_issued`, `hitl.validation_failed`, `hitl.timeout`                                |
| Post-mortem | `postmortem.drafted`, `postmortem.published`                                                 |
| Agent       | `agent.started`, `agent.kill_switch_activated`                                               |
| LLM         | `llm.request`, `llm.response`, `llm.schema_validation_failed`                                |
| PII         | `pii.masked`                                                                                 |
| Audit       | `audit.mapping_table_destroyed`                                                              |

---

## Loki Label Set (spec 09)

Loki labels must be low-cardinality. Only three labels are indexed:

```
{service="<service-name>", env="<local|staging|production>", level="<INFO|WARN|ERROR>"}
```

All other fields are stored in the log line body and queried with `|= "..."` or `| json`.

**Never use** `incident_id`, `trace_id`, or `user_id` as Loki labels — they are high-cardinality and will cause index bloat.

---

## Retention (spec 09)

| Environment | Retention | Storage backend      |
| ----------- | --------- | -------------------- |
| Local       | None      | stdout only          |
| Staging     | 7 days    | Loki                 |
| Production  | 90 days   | Loki + GCS cold      |
| Audit trail | 2 years   | GCS WORM Object Lock |
