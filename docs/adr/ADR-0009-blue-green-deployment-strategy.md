# ADR-0009: Blue-Green Deployment as Default Release Strategy

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / Researcher)
**Affected RQs**: RQ1 (SDLC governance), RQ2 (SLO protection during releases)

---

## Context

The Agentic AI Copilot is an incident response system — it is most needed during
outages. A deployment strategy that itself causes downtime or degrades reliability
during the release window is self-defeating: it would worsen the very metrics
(MTTD, MTTR) the system is designed to improve.

Requirements for the deployment strategy:

1. **Zero-downtime releases** — SLO error budget must not be consumed by deployments.
2. **Instant rollback** — if a newly deployed version is defective, rollback must
   complete in seconds, not minutes (traffic switch, not re-deploy).
3. **Pre-production validation gate** — the new version must be fully validated
   (staging gate, harness/staging-check.yml) before any production traffic is shifted.
4. **Deterministic evaluation environment** — the dissertation evaluation experiments
   must run on a stable version; deployment must not change the version under test
   mid-experiment.
5. **Compatibility with HITL controls** — in-flight HITL approval requests must not
   be lost during a deployment; the active approval queue must be drained or migrated
   before traffic switch.

## Decision

We adopt **Blue-Green Deployment** as the default release strategy for all production
releases.

### Mechanism

```
                         ┌─────────────────┐
                         │   Load Balancer  │
                         └────────┬────────┘
                                  │ 100% traffic
                    ┌─────────────▼──────────────┐
                    │        Blue (active)         │
                    │   version N (current)        │
                    └──────────────────────────────┘

                    ┌──────────────────────────────┐
                    │        Green (idle)           │
                    │   version N+1 (deploying)     │
                    └──────────────────────────────┘
```

**Release sequence:**

1. Deploy version N+1 to the Green environment (zero traffic).
2. Run staging gate (`harness/staging-check.yml`) against Green — full test suite,
   DAST, smoke tests, Golden Signals baseline.
3. If staging gate passes: drain in-flight HITL approval requests from Blue.
4. Switch load balancer: 100% traffic → Green. Blue becomes idle.
5. Monitor Green for 15 minutes (Golden Signals: error rate, latency p99, saturation).
6. If healthy: decommission Blue. If degraded: switch back to Blue (rollback < 30s).

**Rollback SLA:** < 30 seconds (load balancer traffic switch only — no re-deploy).

**HITL drain policy:** Before every traffic switch, the OrchestratorAgent checks for
pending HITL approval tokens. If any are active, the switch is delayed up to 5 minutes
for drain. After 5 minutes, active tokens are migrated to the new version's queue.

### Scope

Blue-Green applies to:

- All agent services (`src/agents/`)
- API gateway (`src/api/`)
- OrchestratorAgent

Infrastructure components (databases, message broker, observability backends) use
independent migration strategies (not in scope of this ADR).

## Alternatives Considered

| Alternative                    | Pros                                                                                          | Cons                                                                                    |
| ------------------------------ | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Rolling update**             | Resource-efficient; gradual rollout                                                           | Mixed-version traffic during rollout; harder to reason about HITL state across versions |
| **Canary release**             | Progressive risk reduction; real-traffic validation                                           | Requires traffic splitting infrastructure; complex for a research prototype             |
| **Recreate (stop-then-start)** | Simplest to implement                                                                         | Downtime during deployment; directly harms MTTD/MTTR metrics                            |
| **Blue-Green** ✅              | Zero downtime; instant rollback; clean version boundary; deterministic evaluation environment | Requires 2× compute during deployment window; HITL drain adds complexity                |
| **Feature flags only**         | Zero deployment risk                                                                          | Requires full feature-flag infrastructure; out of scope                                 |

## Consequences

**Positive:**

- Zero downtime: SLO error budget not consumed by planned releases.
- Rollback < 30 seconds: incident response capability restored immediately if a
  bad release is detected.
- Deterministic evaluation: each experiment runs on exactly one version; no
  mid-experiment deployment changes the system under test.
- HITL drain policy ensures no approval request is lost during deployment — required
  for EU AI Act Art. 14 (human oversight continuity).

**Negative / Trade-offs:**

- 2× compute cost during the deployment window (~15–20 minutes); acceptable for a
  research prototype with bounded evaluation window.
- HITL drain logic adds implementation complexity to the OrchestratorAgent — must be
  tested before any production deployment.
- Stateful components (in-flight incident state) require careful migration if Blue and
  Green differ in state schema — schema migrations must be backwards-compatible.

## Review Criteria

Revisit this decision if:

- Cloud compute cost becomes a constraint (e.g. research budget) — consider Canary
  as a lower-cost alternative with progressive traffic shift.
- The evaluation experiment design requires mid-experiment version changes — introduce
  a versioned experiment namespace that isolates deployment from evaluation traffic.

## References

- Kim, G., Humble, J., Debois, P., Willis, J. (2016). _The DevOps Handbook_. IT Revolution Press.
- Google SRE Book (2016). Chapter 8 — Release Engineering.
- EU AI Act (2024) Art. 14 — Human oversight measures
- `docs/adr/ADR-0004-multi-agent-orchestration-pattern.md` — HITL drain requirement
- `docs/adr/ADR-0007-pr-merge-gates-ci-checks.md` — staging gate prerequisite
- `specs/sdlc/08-deployment-strategy.md` — deployment spec (to be authored, issue #10)
- `harness/staging-check.yml` — staging gate config (to be authored, issue #21)
