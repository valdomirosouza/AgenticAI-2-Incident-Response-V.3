# Spec 10: Tracing Schema

**Domain**: observability
**Owner**: SRE Lead
**Status**: Approved
**Date**: 2026-05-17
**Issue**: #11
**Linked ADRs**: ADR-0012
**Review cadence**: Quarterly or on agent architecture change

---

## 1. Purpose

Define span naming conventions, mandatory span attributes, sampling strategy per
criticality level and the W3C TraceContext propagation contract for all agent hops
in the Copilot.

---

## 2. Context

ADR-0012 adopted OpenTelemetry with W3C TraceContext propagation and OTLP export to
Jaeger/Tempo. Distributed tracing is the primary tool for reconstructing incident
timelines (spec 03) and diagnosing multi-agent latency. Without a consistent span naming
convention, traces are unqueryable and the audit trail reconstruction (ADR-0024) cannot
correlate spans to audit events.

---

## 3. Decision

### 3.1 Span naming convention

Pattern: `<service>/<operation>`

| Service prefix  | Operations (examples)                                      |
| --------------- | ---------------------------------------------------------- |
| `orchestrator`  | `orchestrator/route`, `orchestrator/state_transition`      |
| `detection`     | `detection/anomaly_scan`, `detection/incident_create`      |
| `triage`        | `triage/classify_severity`, `triage/notify_oncall`         |
| `rca`           | `rca/build_hypothesis`, `rca/score_confidence`             |
| `remediation`   | `remediation/propose_action`, `remediation/execute_action` |
| `postmortem`    | `postmortem/draft`, `postmortem/publish`                   |
| `llm_adapter`   | `llm_adapter/sanitize`, `llm_adapter/complete`             |
| `hitl`          | `hitl/request_approval`, `hitl/validate_token`             |
| `audit`         | `audit/write_event`, `audit/compute_hash`                  |
| `observability` | `observability/query_metrics`, `observability/query_logs`  |

Span names are **snake_case**, lowercase. No dynamic values (IDs, timestamps) in the
span name — those go in attributes.

### 3.2 Mandatory span attributes

Every span must carry the following attributes:

| Attribute           | Type   | Source                    | PII risk | Masking rule                                       |
| ------------------- | ------ | ------------------------- | -------- | -------------------------------------------------- |
| `service.name`      | string | OTel SDK resource         | None     | —                                                  |
| `service.version`   | string | OTel SDK resource         | None     | —                                                  |
| `incident.id`       | string | OrchestratorAgent context | None     | —                                                  |
| `agent.role`        | string | Agent self-identifier     | None     | —                                                  |
| `agent.action_type` | string | Action being traced       | None     | Controlled vocabulary (see §3.3)                   |
| `llm.model`         | string | LLM adapter config        | None     | —                                                  |
| `llm.token_count`   | int    | LLM response metadata     | None     | —                                                  |
| `pii.sanitized`     | bool   | PII sanitizer result      | None     | — (must be `true` on llm spans)                    |
| `http.method`       | string | HTTP instrumentation      | None     | —                                                  |
| `http.status_code`  | int    | HTTP instrumentation      | None     | —                                                  |
| `user.id`           | string | Request context           | **High** | Replace with pseudonymised `usr_<hash>` (ADR-0014) |

**Forbidden attributes** — must never appear in any span:

- `user.email`, `user.name`, `user.ip_address`
- `llm.prompt` (raw prompt content — only `llm.token_count` and `pii.sanitized`)
- `llm.response` (raw response content)
- Any field containing CPF, CNPJ, credit card numbers

The OTel SpanProcessor (ADR-0014) enforces these exclusions at the application layer.

### 3.3 Action type vocabulary (`agent.action_type`)

Controlled vocabulary for the `agent.action_type` attribute:

```
ANOMALY_SCAN         INCIDENT_CREATE       SEVERITY_CLASSIFY
ONCALL_NOTIFY        RCA_BUILD             RCA_SCORE
REMEDIATION_PROPOSE  REMEDIATION_EXECUTE   HITL_REQUEST
HITL_VALIDATE        POSTMORTEM_DRAFT      POSTMORTEM_PUBLISH
LLM_SANITIZE         LLM_COMPLETE          AUDIT_WRITE
STATE_TRANSITION     KILL_SWITCH
```

### 3.4 W3C TraceContext propagation

All inter-agent calls (in-process and HTTP) propagate W3C TraceContext headers:

```
traceparent: 00-{trace_id}-{span_id}-{flags}
tracestate:  copilot=<incident_id>
```

The `tracestate` extension carries `incident_id` so that all spans for a given incident
can be retrieved with a single Tempo query:

```
{tracestate=~"copilot=inc-.*"} | incident_id = "inc-2026-0517-001"
```

In-process agent calls use OTel context propagation (`context.attach`). HTTP calls
inject `traceparent` via the OTel HTTP propagator middleware.

### 3.5 Sampling strategy

| Scenario                                     | Sampling rate | Rationale                                      |
| -------------------------------------------- | ------------- | ---------------------------------------------- |
| Active incident (incident_id set in context) | 100%          | Full fidelity required for RCA and audit trail |
| HITL approval flow                           | 100%          | Compliance requirement — every approval traced |
| Background health checks / scrape requests   | 1%            | High volume; low diagnostic value              |
| LLM adapter calls                            | 100%          | Latency and token budget tracking              |
| All other traffic (no incident context)      | 10%           | Balanced cost vs. coverage                     |

Sampling decisions are made by the OTel SDK head-based sampler configured in
`infrastructure/otel-collector-config.yaml`.

Tail-based sampling (Tempo) retains 100% of traces containing an error span regardless
of head sampling rate — ensuring no error trace is lost.

### 3.6 Agent hop trace example

Full trace for a P1 incident detection → HITL approval → remediation:

```
[orchestrator/route]  trace_id=abc123  duration=2ms
  ├─ [detection/anomaly_scan]           duration=1 200ms
  │    └─ [observability/query_metrics] duration=800ms
  ├─ [triage/classify_severity]         duration=450ms
  │    └─ [llm_adapter/complete]        duration=380ms
  │         └─ [llm_adapter/sanitize]   duration=55ms
  ├─ [rca/build_hypothesis]             duration=2 100ms
  │    ├─ [observability/query_logs]    duration=700ms
  │    └─ [llm_adapter/complete]        duration=1 200ms
  ├─ [remediation/propose_action]       duration=320ms
  │    └─ [llm_adapter/complete]        duration=290ms
  ├─ [hitl/request_approval]            duration=4m 32s  ← includes human wait time
  │    └─ [hitl/validate_token]         duration=12ms
  └─ [remediation/execute_action]       duration=8 200ms
       └─ [audit/write_event]           duration=25ms
```

`duration_ms` in the corresponding log lines matches the span duration for
cross-signal correlation.

### 3.7 Privacy Impact

- `user.id` is pseudonymised by the OTel SpanProcessor before the span is exported
  (ADR-0014). The mapping table lives in Vault (ADR-0020).
- Raw `llm.prompt` and `llm.response` are explicitly excluded from all spans
  (ADR-0028 and ADR-0030 — prompts never persisted).
- Trace data is retained for 14 days (ADR-0030) and subject to erasure requests
  within 15 days (LGPD art. 18).

---

## 4. Acceptance Criteria

- [ ] Span naming pattern `<service>/<operation>` defined with examples for all 6 agent services + 4 infrastructure services
- [ ] Mandatory attribute table covers all 11 attributes with PII risk and masking rule
- [ ] Forbidden attributes explicitly listed (raw prompt/response, PII fields)
- [ ] `agent.action_type` controlled vocabulary has ≥ 15 values
- [ ] W3C TraceContext propagation defined including `tracestate` extension for `incident_id`
- [ ] Sampling strategy covers 5 scenarios including 100% for active incidents and HITL flows
- [ ] End-to-end trace example shows all agent hops from detection through remediation
- [ ] Privacy Impact references ADR-0014, ADR-0020, ADR-0028, ADR-0030
- [ ] Language: English only (RULE-005)

---

## 5. Linked ADRs

| ADR      | Relevance                                                                 |
| -------- | ------------------------------------------------------------------------- |
| ADR-0012 | OpenTelemetry instrumentation — W3C TraceContext, OTLP, SDK config        |
| ADR-0014 | PII masking — `user.id` pseudonymisation; forbidden attribute enforcement |
| ADR-0020 | Vault — pseudonymisation mapping storage                                  |
| ADR-0024 | Immutable audit trail — `trace_id`/`span_id` in every audit event         |
| ADR-0028 | PII sanitization — `llm.prompt` excluded from spans                       |
| ADR-0030 | Data retention — 14-day trace TTL                                         |

---

## References

- `docs/adr/ADR-0012-opentelemetry-instrumentation-standard.md`
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md`
- `specs/observability/09-logging-schema.md` — `trace_id`/`span_id` format shared with logs
- `specs/system/03-incident-lifecycle.md` — lifecycle stages mapped to span sequence
