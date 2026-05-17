# Skill: Traces

**Domain**: observability
**Activation triggers**: Distributed tracing, OpenTelemetry, span, trace, RCA, trace schema, W3C TraceContext, sampling, trace attributes, Tempo
**References**: specs/observability/10-tracing-schema.md, ADR-0012, ADR-0014

---

## Span Naming Convention

```
<service>/<operation>

Examples:
  triage-agent/classify-severity
  rca-agent/build-hypothesis
  remediation-agent/propose-action
  llm-adapter/complete
  action-executor/execute
  hitl-gate/validate-token
  pii-sanitizer/sanitize
```

Rule: `service` matches the `src/` subdirectory name; `operation` is `kebab-case` verb-noun.

---

## Mandatory Span Attributes (11 fields)

| Attribute           | Type   | Description                                         | PII risk | Rule                        |
| ------------------- | ------ | --------------------------------------------------- | -------- | --------------------------- |
| `service.name`      | string | Service name (matches log `service` field)          | No       | Mandatory                   |
| `incident.id`       | string | Active incident ID or `"none"`                      | No       | Mandatory                   |
| `agent.name`        | string | Agent class name or `"none"`                        | No       | Mandatory                   |
| `agent.action_type` | string | Action type from vocabulary (see below) or `"none"` | No       | Mandatory                   |
| `autonomy.level`    | string | `HITL` / `HOTL` / `BLOCKED` / `none`                | No       | Mandatory                   |
| `hitl.token_id`     | string | ApprovalToken UUID or `"none"` if HOTL              | No       | Mandatory for HITL spans    |
| `llm.model`         | string | LLM model ID or `"none"`                            | No       | Mandatory for LLM spans     |
| `llm.sanitized`     | bool   | Whether PII sanitization was applied                | No       | Mandatory for LLM spans     |
| `audit.event_type`  | string | Audit event written in this span or `"none"`        | No       | Mandatory                   |
| `error`             | bool   | `true` if span ended in error                       | No       | Mandatory                   |
| `error.type`        | string | Exception class name or `"none"`                    | No       | Mandatory when `error=true` |

### Forbidden attributes (ADR-0014)

Never set these on spans — they constitute PII:

- Raw LLM prompt or response text
- User email, name, or real identifier
- IP address (only subnet `/24` permitted)
- CPF, CNPJ, phone number

---

## Action Type Vocabulary (17 values)

Used for `agent.action_type` attribute. Adding a new value requires a spec update.

| Category    | Values                                                                                                                                                                  |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Detection   | `DETECT_ANOMALY`                                                                                                                                                        |
| Triage      | `CLASSIFY_SEVERITY`, `NOTIFY_ONCALL`                                                                                                                                    |
| RCA         | `QUERY_LOGS`, `QUERY_TRACES`, `BUILD_HYPOTHESIS`                                                                                                                        |
| Remediation | `PROPOSE_ACTION`, `PRODUCTION_scale_replicas`, `PRODUCTION_restart_service`, `PRODUCTION_shift_traffic`, `PRODUCTION_rollback_deploy`, `PRODUCTION_toggle_feature_flag` |
| Blocked     | `PRODUCTION_data_delete`, `PRODUCTION_iam_change`, `PRODUCTION_firewall_change`                                                                                         |
| Post-mortem | `DRAFT_POSTMORTEM`                                                                                                                                                      |

---

## W3C TraceContext Extension

The `tracestate` header carries the incident ID across all agent hops:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: copilot=inc-2026-0517-003
```

This allows Tempo to correlate all spans for a single incident regardless of which agent or adapter produced them.

---

## Sampling Strategy (spec 10)

| Scenario                         | Sample rate | Rationale                                     |
| -------------------------------- | ----------- | --------------------------------------------- |
| P1 active incident               | 100%        | Full fidelity for post-mortem reconstruction  |
| P2 active incident               | 100%        | Same                                          |
| P3/P4 incident                   | 20%         | Reduce storage; sufficient for trend analysis |
| HITL gate validation             | 100%        | Always traced — audit requirement             |
| LLM adapter calls                | 100%        | Always traced — schema validation evidence    |
| Health checks / readiness probes | 0%          | No value; reduces noise                       |
| Background tasks (no incident)   | 5%          | Baseline profiling only                       |

---

## End-to-End Agent Hop Example

```
Span: orchestrator-agent/handle-alert          [trace_id: 4bf9...] [incident_id: inc-2026-0517-003]
  ├── Span: triage-agent/classify-severity      [autonomy: HOTL]
  │     ├── Span: pii-sanitizer/sanitize        [llm.sanitized: false → true]
  │     └── Span: llm-adapter/complete          [llm.model: claude-sonnet-4-6, llm.sanitized: true]
  ├── Span: rca-agent/build-hypothesis          [autonomy: HOTL]
  │     ├── Span: loki-adapter/query-logs       [action_type: QUERY_LOGS]
  │     ├── Span: tempo-adapter/query-traces    [action_type: QUERY_TRACES]
  │     └── Span: llm-adapter/complete          [llm.sanitized: true]
  └── Span: remediation-agent/propose-action    [autonomy: HITL]
        ├── Span: hitl-gate/validate-token      [hitl.token_id: uuid, audit.event_type: hitl.token_issued]
        └── Span: action-executor/execute       [action_type: PRODUCTION_scale_replicas]
```

---

## OpenTelemetry Instrumentation (Python)

```python
from opentelemetry import trace
from opentelemetry.trace import SpanKind

tracer = trace.get_tracer("triage-agent")

def classify_severity(incident_id: str, metrics: MetricSnapshot) -> SeverityResult:
    with tracer.start_as_current_span(
        "triage-agent/classify-severity",
        kind=SpanKind.INTERNAL,
        attributes={
            "incident.id": incident_id,
            "agent.name": "TriageAgent",
            "agent.action_type": "CLASSIFY_SEVERITY",
            "autonomy.level": "HOTL",
            "hitl.token_id": "none",
            "llm.model": "none",
            "llm.sanitized": False,
            "audit.event_type": "incident.severity_set",
            "error": False,
            "error.type": "none",
        }
    ) as span:
        try:
            result = _do_classify(metrics)
            span.set_attribute("agent.confidence", result.confidence)
            return result
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            span.record_exception(e)
            raise
```

---

## Querying in Tempo

```
# Find all spans for an incident
{incident.id="inc-2026-0517-003"}

# Find all HITL validations that failed
{agent.action_type="HITL_VALIDATE" error=true}

# Find slow LLM calls (> 8s)
{service.name="llm-adapter" duration > 8s}
```
