# ADR-0012: OpenTelemetry as Unified Instrumentation Standard

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (observability architecture), RQ2 (MTTD reduction), RQ4 (auditability)

---

## Context

The Copilot and all observed services must emit telemetry (traces, metrics, logs) that:

1. **Correlates across services** — a single incident event must produce a `trace_id`
   that links the alert in DetectionAgent, the LLM call in TriageAgent, and the
   remediation action in RemediationAgent into a single causal chain. Without this,
   the PostMortemAgent cannot reconstruct the incident timeline.
2. **Is backend-agnostic** — the observability backend (Prometheus, Jaeger, Grafana,
   Datadog) must be swappable without re-instrumenting application code. This is
   required for both the research prototype (low cost) and a future production
   deployment (operational preference).
3. **Satisfies audit trail requirements** — EU AI Act Art. 12 requires that all agent
   actions be logged and traceable. Each agent action must carry a `trace_id` and
   `span_id` that links it to the triggering incident event.
4. **Is vendor-neutral and standardised** — using a CNCF standard ensures that the
   instrumentation approach is reproducible, well-documented, and avoids proprietary
   lock-in that could invalidate the dissertation's replication package.
5. **Supports the W3C TraceContext standard** — cross-service trace propagation must
   follow W3C TraceContext (RFC) so that `trace_id` is consistent across HTTP, gRPC
   and message broker boundaries.

## Decision

We adopt **OpenTelemetry (OTel)** as the unified instrumentation standard for all
telemetry (traces, metrics, logs) in this project.

### Instrumentation architecture

```
Application code (agents, API, guardrails)
        │ OTel SDK (Python opentelemetry-sdk)
        ▼
OTel Collector (sidecar / DaemonSet)
        │ OTLP gRPC
        ├──► Prometheus (metrics scrape endpoint)
        ├──► Jaeger / Tempo (traces)
        └──► Loki / Cloud Logging (logs)
```

### Mandatory instrumentation per agent service

Every agent service must instrument:

| Signal      | What to instrument                                                                    | OTel primitive                                      |
| ----------- | ------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Traces**  | Every inbound request, every outbound port call (LLM, DB, metrics backend)            | `Span` with `trace_id`, `span_id`, `parent_span_id` |
| **Metrics** | Golden Signals per service (ADR-0011), LLM call latency/tokens, guardrail invocations | `Counter`, `Histogram`, `Gauge`                     |
| **Logs**    | Structured JSON log (ADR-0013) with `trace_id` and `span_id` injected automatically   | Log bridge (OTel → log backend)                     |

### Context propagation rules

- **W3C TraceContext** (`traceparent` / `tracestate` headers) is the mandatory
  propagation format for all HTTP and gRPC calls.
- **Baggage** propagation is used for incident context (`incident_id`, `severity`)
  across service boundaries.
- The OrchestratorAgent generates the root `trace_id` at incident creation and passes
  it to all specialist agents. Every agent action is a child span of this root trace.

### Semantic conventions

All span and metric names follow the **OTel Semantic Conventions** (OTEL-SEMCONV):

- HTTP spans: `http.method`, `http.status_code`, `http.url`
- LLM spans (custom, based on OTel GenAI conventions): `llm.provider`, `llm.model`,
  `llm.input_tokens`, `llm.output_tokens`, `llm.request_duration_ms`
- Agent spans (custom): `agent.name`, `agent.action`, `incident.id`, `incident.severity`

### Sampling strategy

- **Development:** 100% sampling (all traces collected).
- **Production / evaluation:** Head-based sampling at 10% for routine traffic;
  100% sampling for P1 and P2 incidents (tail sampling by `incident.severity` attribute).

## Alternatives Considered

| Alternative                     | Pros                                                                                               | Cons                                                                                                           |
| ------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Prometheus + custom tracing** | Prometheus is the de-facto metrics standard                                                        | No unified traces/logs/metrics model; custom tracing is non-standard; breaks EU AI Act audit trail requirement |
| **Datadog APM (proprietary)**   | Full-stack observability; low setup time                                                           | Vendor lock-in; cost at scale; cannot be included in open dissertation replication package                     |
| **Jaeger SDK (direct)**         | Mature tracing                                                                                     | Metrics not covered; deprecated in favour of OTel                                                              |
| **OpenTelemetry** ✅            | CNCF standard; traces + metrics + logs unified; backend-agnostic; W3C compliant; Python SDK mature | OTel Collector adds operational complexity; Python SDK auto-instrumentation coverage varies by library         |

## Consequences

**Positive:**

- Single `trace_id` links DetectionAgent alert → TriageAgent analysis → LLM call →
  RemediationAgent action → human approval — complete EU AI Act Art. 12 audit trail
  by construction.
- Backend swap (Jaeger → Tempo, Prometheus → Mimir) requires only Collector config
  change — zero application code change.
- OTel Python auto-instrumentation covers `requests`, `httpx`, `sqlalchemy`, `grpc` —
  ports are instrumented with minimal manual code.
- W3C TraceContext compliance ensures `trace_id` propagates correctly across all
  service boundaries, including external runbook APIs.

**Negative / Trade-offs:**

- OTel Collector adds an operational component to manage in the evaluation environment —
  mitigated by using the `opentelemetry-sdk` direct exporter in development mode
  (no Collector required).
- OTel Python SDK is still maturing for logs — log bridge to Loki may require manual
  configuration. Documented in `specs/observability/10-tracing-schema.md`.

## Review Criteria

Revisit this decision if:

- OTel Python SDK introduces a breaking change to the GenAI semantic conventions that
  requires significant re-instrumentation — evaluate upgrade cost vs. stability.
- The evaluation environment cannot run an OTel Collector (resource constraint) —
  use direct OTLP export to Jaeger/Prometheus without Collector as an exception.

## References

- OpenTelemetry Project — opentelemetry.io (CNCF)
- W3C TraceContext Recommendation — w3.org/TR/trace-context
- OTel Semantic Conventions — opentelemetry.io/docs/concepts/semantic-conventions
- EU AI Act (2024) Art. 12 — Record-keeping requirements
- `docs/adr/ADR-0011-golden-signals-canonical-metric-set.md` — metrics instrumented via OTel
- `docs/adr/ADR-0013-structured-json-logging-schema.md` — log format with OTel context fields
- `docs/adr/ADR-0014-pii-masking-observability-pipelines.md` — masking applied before OTel export
- `specs/observability/10-tracing-schema.md` — tracing schema spec (to be authored, issue #11)
