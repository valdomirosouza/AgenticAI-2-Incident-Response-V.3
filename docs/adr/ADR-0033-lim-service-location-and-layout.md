# ADR-0033: LIM Service Location and Project Layout

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Tech Lead, SRE Lead
**Affected RQs**: RQ1, RQ2

---

## Context

The Log-Ingestion-and-Metrics (LIM) sub-project introduces a new FastAPI service
that ingests HAProxy logs and exposes Golden Signal analytics. A decision is required
on where to place this service within the repository and how to structure its internal
layout so that it remains independently deployable, testable and aligned with the
existing hexagonal architecture standard (ADR-0002).

Two placement options were evaluated: (a) inside the existing `src/` tree alongside
the agent code, or (b) as a separate top-level service directory under `services/`.

The key constraint is that the LIM service has its own `pyproject.toml`, its own
Docker build context, and its own dependency set (FastAPI + redis-py + opentelemetry).
Co-locating it inside `src/` would merge those concerns with the agent runtime and
complicate independent builds and deployments.

---

## Decision

The `log-ingestion-and-metrics` service is placed at
`services/log-ingestion-and-metrics/` as a standalone Python package with its own
`pyproject.toml`. The internal layout follows the hexagonal pattern mandated by
ADR-0002:

```
services/log-ingestion-and-metrics/
├── pyproject.toml
├── specs/
│   ├── log-ingestion-api.md    (Spec LIM-01)
│   └── analytics-api.md       (Spec LIM-02)
├── src/
│   ├── domain/
│   │   ├── models/             (HaproxyLogEntry, MetricPoint, SignalType)
│   │   └── services/           (LogParser, PercentileService)
│   ├── ports/                  (MetricStorePort, IngestionPort — ABCs)
│   ├── adapters/               (RedisMetricAdapter)
│   ├── api/
│   │   ├── main.py             (FastAPI app entrypoint)
│   │   └── routers/            (ingestion.py, analytics.py, health.py)
│   └── observability/          (OTel instrumentation)
└── tests/
    ├── unit/
    └── integration/
```

The `services/` prefix signals to CI, Docker and Helm that this is a deployable
service boundary. Future services (e.g., `services/remediation-executor/`) follow
the same pattern without changes to the root `src/` tree.

---

## Alternatives Considered

| Alternative                                    | Pros                                                                    | Cons                                                                                    |
| ---------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Place under `src/services/lim/`                | Single repo root; shared tooling                                        | Mixes agent runtime deps with service deps; single Docker build context                 |
| Standalone repo (separate git repo)            | True isolation; independent CI                                          | Adds overhead for a university research project; complicates ADR/spec cross-referencing |
| `services/log-ingestion-and-metrics/` (chosen) | Clean boundary; independent pyproject.toml; follows ADR-0002 internally | Slightly deeper path; requires `services/` prefix awareness in CI                       |

---

## Consequences

**Positive:**

- The LIM service can be built, tested and deployed independently with no coupling to the agent runtime.
- Internal hexagonal layout (domain → ports → adapters → api) makes the `RedisMetricAdapter` swappable for any other metric store without touching domain logic.
- CI can scope LIM-specific checks to `services/log-ingestion-and-metrics/**` path filters.

**Negative / Trade-offs:**

- Two `pyproject.toml` files (root and LIM service) must be kept aligned on shared conventions (Python version, linting rules).
- PR reviewers must be aware of the `services/` boundary to avoid accidentally importing LIM internals from `src/`.

---

## Review Criteria

Revisit if: (a) a second service is added under `services/` and the pattern proves inadequate, or (b) the project migrates to a monorepo toolchain (Pants, Bazel) that changes directory semantics.

---

## References

- ADR-0002: Hexagonal Architecture as the structural pattern for agent services
- Spec LIM-01: `services/log-ingestion-and-metrics/specs/log-ingestion-api.md`
- Spec LIM-02: `services/log-ingestion-and-metrics/specs/analytics-api.md`
- Issue [#59](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/59), Issue [#60](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/60)
