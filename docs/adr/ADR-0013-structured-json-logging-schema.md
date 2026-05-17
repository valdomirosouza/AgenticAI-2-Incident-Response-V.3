# ADR-0013: Structured JSON Logging with Mandatory Fields

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (observability architecture), RQ4 (audit trail, compliance)

---

## Context

Logs are one of three observability pillars (along with metrics and traces). For the
Copilot to function correctly, logs must be:

1. **Machine-parseable** — the PostMortemAgent and RCAAgent query logs to reconstruct
   incident timelines. Free-text logs require expensive NLP extraction; structured logs
   are directly queryable by field.
2. **Audit-complete** — ISO 27001 A.12.4 (Logging and monitoring) requires that audit
   logs capture who did what, when, and with what outcome. LGPD art. 48 requires that
   breach notification include a description of the affected data — logs are the primary
   source for this description.
3. **Traceable** — every log line must carry the `trace_id` and `span_id` from the
   OpenTelemetry context (ADR-0012) so that logs and traces can be joined in the
   observability backend.
4. **PII-safe by default** — logs must never contain raw PII. The mandatory field set
   defines `user_id` as an opaque identifier (pseudonymised or anonymised) — never a
   name, email or other direct identifier (ADR-0014).
5. **Consistent across all services** — a single schema enables cross-service log
   aggregation and correlation without per-service parsing rules.

## Decision

All log lines emitted by any component of this system must use **structured JSON format**
with the following mandatory fields.

### Mandatory log schema

```json
{
  "timestamp": "2026-05-17T14:23:01.456Z",
  "level": "INFO",
  "service": "triage-agent",
  "version": "0.3.1",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "incident_id": "INC-2026-0042",
  "message": "Triage completed: severity P2, confidence 0.87",
  "event": "triage.completed",
  "duration_ms": 1240,
  "user_id": "usr_a3f9b2c1"
}
```

### Mandatory field definitions

| Field         | Type                                               | Required                 | Description                                          |
| ------------- | -------------------------------------------------- | ------------------------ | ---------------------------------------------------- |
| `timestamp`   | ISO 8601 UTC string                                | Always                   | Log emission time, microsecond precision             |
| `level`       | enum: `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL` | Always                   | Log severity                                         |
| `service`     | string (kebab-case)                                | Always                   | Emitting service name                                |
| `version`     | semver string                                      | Always                   | Service version at emit time                         |
| `trace_id`    | 32-char hex (W3C)                                  | Always                   | OTel trace ID — links log to trace                   |
| `span_id`     | 16-char hex (W3C)                                  | Always                   | OTel span ID — links log to span                     |
| `message`     | string                                             | Always                   | Human-readable description of the event              |
| `event`       | string (dot-notation)                              | Always                   | Machine-readable event code, e.g. `triage.completed` |
| `incident_id` | string                                             | When in incident context | Incident identifier for cross-signal join            |
| `user_id`     | opaque string                                      | When user context exists | Pseudonymised user identifier — never name/email     |
| `duration_ms` | integer                                            | For timed operations     | Operation duration in milliseconds                   |

### Optional contextual fields

Additional fields are allowed (e.g. `llm_model`, `tokens_used`, `action_type`) but
must not contain PII. Any field added must be documented in
`specs/observability/09-logging-schema.md`.

### Log levels policy

| Level      | When to use                                                     |
| ---------- | --------------------------------------------------------------- |
| `DEBUG`    | Detailed diagnostic information — disabled in production        |
| `INFO`     | Normal operational events (agent lifecycle, state transitions)  |
| `WARN`     | Recoverable anomalies (retry, fallback, low-confidence triage)  |
| `ERROR`    | Failures requiring attention (adapter error, guardrail trigger) |
| `CRITICAL` | System-threatening failures (HITL gate failure, data breach)    |

`DEBUG` logs are suppressed in production by the OTel Collector pipeline.
`CRITICAL` logs trigger an immediate alert to the on-call channel (ADR-0015).

### Prohibited content

- **PII** (name, email, phone, IP address, device ID) — use `user_id` (opaque)
  or remove entirely. Enforced by PR gate G10 (ADR-0007) and PII masking (ADR-0014).
- **Secrets** (API keys, tokens, passwords) — enforced by PR gate G03 (ADR-0007).
- **Raw stack traces in INFO/WARN** — stack traces go in `ERROR`/`CRITICAL` only,
  and must be stripped of file paths that expose directory structure.

## Alternatives Considered

| Alternative                             | Pros                                                                        | Cons                                                                                            |
| --------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Free-text logs**                      | Zero authoring overhead                                                     | Not machine-parseable; PostMortemAgent/RCAAgent cannot query; ISO 27001 audit requirement unmet |
| **Logfmt (key=value)**                  | Human-readable; structured                                                  | Less widely supported than JSON in log aggregators; schema not formally enforceable             |
| **Structured JSON (custom schema)**     | Tailored to project                                                         | Non-standard field names confuse tooling; no interoperability                                   |
| **Structured JSON with OTel fields** ✅ | Machine-parseable; OTel trace join; ISO 27001 compliant; PII-safe by schema | Slightly more verbose than free-text; `trace_id` / `span_id` must be injected from OTel context |

## Consequences

**Positive:**

- PostMortemAgent queries `incident_id` across logs, metrics and traces — incident
  timeline reconstruction requires zero NLP, only field projection and time-sort.
- `trace_id` / `span_id` in every log line enables log-trace join in Grafana/Jaeger
  without additional configuration.
- ISO 27001 A.12.4: audit log schema is formally defined and version-controlled.
- LGPD art. 48: breach notification can be drafted from structured logs without
  manual extraction — `incident_id`, `event`, `timestamp` are always present.
- PII field prohibition enforced at schema level — `user_id` as opaque string is
  the only user reference allowed.

**Negative / Trade-offs:**

- Mandatory `trace_id` / `span_id` means logging is coupled to OTel context
  injection — any code path that bypasses the OTel SDK must use a nil trace ID
  (`0000...0000`), not omit the field.
- Schema evolution requires a spec change (`specs/observability/09-logging-schema.md`)
  and a CHANGELOG entry — adds process overhead for adding new fields.

## Review Criteria

Revisit this decision if:

- A log aggregator backend is adopted that requires a different field naming convention
  (e.g. Elastic Common Schema) — evaluate migration cost vs. schema alignment.
- The mandatory field set is insufficient for the PostMortemAgent's timeline
  reconstruction accuracy — add fields to the spec without removing mandatory ones.

## References

- ISO/IEC 27001:2022 Annex A, A.12.4 — Logging and monitoring
- LGPD (Lei 13.709/2018) Art. 48 — Communication of security incidents
- W3C TraceContext — w3.org/TR/trace-context (trace_id / span_id format)
- `docs/adr/ADR-0012-opentelemetry-instrumentation-standard.md` — OTel context injection
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md` — PII masking before log ingestion
- `specs/observability/09-logging-schema.md` — full logging schema spec (to be authored, issue #11)
- CLAUDE.md §5 RULE-C03 — no PII in repository files or logs
