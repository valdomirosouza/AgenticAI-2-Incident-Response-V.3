# ADR-0011: Golden Signals as the Canonical Metric Set

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (observability architecture), RQ2 (MTTD reduction)

---

## Context

The DetectionAgent must monitor observability data and fire an incident alert when
service health degrades. For this to work, the project needs a canonical metric set
that is:

1. **Sufficient for detection** — must cover the signals that indicate an incident
   across the majority of cloud-native service failure modes.
2. **Small enough to reason about** — agents and dashboards that monitor too many
   metrics suffer from alert fatigue; humans and models alike need a focused signal.
3. **Universally applicable** — the metric set must apply to any service in the
   system without per-service customisation, so the DetectionAgent can use a single
   evaluation model.
4. **Standardised** — using an industry-standard metric set enables comparison with
   external benchmarks and ensures the dissertation's evaluation methodology is
   reproducible and accepted by the research community.
5. **Aligned with SLO definitions** — the metric set must map directly to SLOs, so
   error budget burn rate can be computed from the same signals used for detection.

ISO 20000-1 (Service Management) requires that IT service monitoring be defined and
maintained; having a documented canonical metric set satisfies this requirement.

## Decision

We adopt the **Four Golden Signals** from the Google SRE Book (Beyer et al., 2016)
as the canonical metric set for all service health monitoring in this project.

### Canonical signal definitions

| Signal         | Definition                                 | Primary metric                                                    | Secondary metrics                           |
| -------------- | ------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------- |
| **Latency**    | Time taken to service a request            | `http_request_duration_seconds` (p50, p95, p99)                   | gRPC `grpc_server_handling_seconds`         |
| **Error Rate** | Fraction of requests resulting in an error | `http_requests_total{status=~"5.."}` / `http_requests_total`      | 4xx rate for client-error SLOs              |
| **Traffic**    | Volume of demand on the system             | `http_requests_total` (req/s)                                     | Event throughput for async services         |
| **Saturation** | How close a resource is to its limit       | `process_cpu_usage`, `process_resident_memory_bytes`, queue depth | Thread pool utilisation, DB connection pool |

### Percentile tracking rule

Latency is **always** tracked at p50, p95 and p99. Mean latency is never used as an
SLO metric — it masks tail latency that affects the worst-affected users (CUJ impact).

### Metric naming convention

All custom metrics follow the Prometheus naming convention:

```
<service>_<subsystem>_<name>_<unit>
```

Example: `triage_agent_llm_call_duration_seconds`

### DetectionAgent evaluation model

The DetectionAgent evaluates all four signals per service every 30 seconds (scrape
interval). An alert fires when any signal crosses its SLO-derived threshold for two
consecutive evaluation windows (ADR-0015).

## Alternatives Considered

| Alternative                                      | Pros                                                                                               | Cons                                                                                                                  |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **RED method** (Rate, Errors, Duration)          | Simpler (3 signals); designed for microservices                                                    | Missing Saturation — resource exhaustion incidents invisible until cascade                                            |
| **USE method** (Utilisation, Saturation, Errors) | Strong for resource monitoring                                                                     | Designed for infrastructure, not services; poor for latency-driven incidents                                          |
| **Custom metric taxonomy**                       | Tailored to this system                                                                            | Not standardised; dissertation comparisons against external benchmarks invalid                                        |
| **Four Golden Signals** ✅                       | Industry standard; covers all major failure modes; maps directly to SLOs; widely cited in research | Four signals can be insufficient for business-level CUJ monitoring — mitigated by CUJ-level composite SLOs (ADR-0015) |

## Consequences

**Positive:**

- DetectionAgent uses a single, well-understood evaluation model applicable to all
  services — reduces false positive rate and simplifies ML model training.
- Golden Signals map directly to SLOs (ADR-0015) — MTTD is triggered when an SLO
  burn rate threshold is crossed, not an arbitrary fixed value.
- Dissertation results are comparable to external SRE benchmarks because the metric
  set is the industry standard.
- ISO 20000-1 compliance: monitoring is formally defined and documented.

**Negative / Trade-offs:**

- Four signals may miss business-level CUJ degradation (e.g. checkout conversion rate
  dropping without a latency spike) — mitigated by adding CUJ-specific composite
  metrics as SLIs per service.
- Saturation metrics require per-resource definition — CPU, memory and queue depth are
  not uniformly available across all runtime environments. Documented in the
  observability spec (issue #11).

## Review Criteria

Revisit this decision if:

- The DetectionAgent evaluation shows that Golden Signals miss > 20% of incidents in
  the evaluation corpus — add a fifth signal or composite SLI.
- A service type (e.g. batch pipeline, ML training job) does not fit the request-based
  model — define an extended signal set for that service type as a supplementary spec.

## References

- Beyer, B. et al. (2016). _Site Reliability Engineering_. O'Reilly. Chapter 6 — Monitoring Distributed Systems.
- ISO/IEC 20000-1:2018 — Service management system requirements
- `docs/adr/ADR-0015-slo-based-alerting-thresholds.md` — SLO thresholds derived from these signals
- `docs/glossary.md` — Golden Signals, Latency, Error Rate, Traffic, Saturation definitions
- `specs/observability/08-golden-signals.md` — instrumentation spec (to be authored, issue #11)
- CLAUDE.md §1.3 — System boundaries (data sources: metrics, Golden Signals)
