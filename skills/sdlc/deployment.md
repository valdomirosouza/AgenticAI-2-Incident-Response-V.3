# Skill: Deployment

**Domain**: sdlc
**Activation triggers**: Deployment, deploy, release, rollback, blue-green, feature flag, production deploy, staging, CD pipeline, rollback trigger, RTO
**References**: specs/sdlc/07-release-process.md, ADR-0009, CLAUDE.md §8

---

## Deployment Strategy: Blue-Green (ADR-0009)

```
                    ┌──────────────────┐
                    │   Load Balancer  │
                    └────────┬─────────┘
                             │ 100% traffic
                    ┌────────▼─────────┐
                    │  GREEN (active)  │  ← current production (v N)
                    └──────────────────┘

During deploy:
                    ┌──────────────────┐
                    │   Load Balancer  │
                    └──┬───────────────┘
           0% traffic  │  100% traffic
      ┌────────────────▼┐ ┌────────────▼─────┐
      │  BLUE (new) v N+1│ │  GREEN (active) v N│
      └─────────────────┘ └──────────────────┘

After validation:
                    ┌──────────────────┐
                    │   Load Balancer  │
                    └────────┬─────────┘
                             │ 100% traffic
                    ┌────────▼─────────┐
                    │  BLUE (active)   │  ← new production (v N+1)
                    └──────────────────┘
           GREEN kept warm for rollback window (15 min)
```

---

## Deploy Checklist (per spec 07)

### Pre-deploy (release gate must be green)

- [ ] All CI gates green on the tagged commit
- [ ] SBOM attached to GitHub Release
- [ ] Bias audit report ≤ 90 days old, `release_gate_pass: true`
- [ ] DPIA/RIPD gate intact (no new high-risk PII processing added)
- [ ] Blue environment deployed and health checks passing
- [ ] Smoke test suite passing on Blue (staging equivalent)

### Traffic cut-over

- [ ] Shift 10% traffic to Blue; monitor Golden Signals for 2 minutes
- [ ] Shift 50% traffic to Blue; monitor for 3 minutes
- [ ] Shift 100% traffic to Blue if SLOs holding
- [ ] Keep Green warm for 15 minutes (immediate rollback window)
- [ ] Decommission Green after 15-minute window if no rollback triggered

### Post-deploy

- [ ] Confirm `incident:mttd_mean_30d` and `incident:mttr_mean_30d` within SLO targets
- [ ] Confirm audit trail write rate > 0 (no silent failures)
- [ ] Confirm HITL queue depth = 0 (no stuck approvals)
- [ ] Alert team in Slack `#deployments` with version and deploy time

---

## Rollback Triggers (ADR-0009)

Initiate rollback immediately (shift 100% traffic back to Green) when:

| Trigger                                | RTO target   |
| -------------------------------------- | ------------ |
| Error rate > SLO threshold for > 2 min | < 5 minutes  |
| Latency p99 > 2× SLO for > 2 min       | < 5 minutes  |
| Audit trail write failure (any)        | < 2 minutes  |
| HITL gate returning unexpected errors  | < 2 minutes  |
| Kill-switch activated                  | < 60 seconds |

Rollback procedure:

1. Shift 100% traffic back to Green immediately.
2. Write `deployment.rollback` audit event with reason.
3. Open P1 incident automatically.
4. File post-mortem within 24 hours.

---

## Environment Ladder

| Environment  | Purpose                           | Deploy trigger                    | HITL enforced |
| ------------ | --------------------------------- | --------------------------------- | ------------- |
| `local`      | Developer testing                 | Manual (`docker-compose up`)      | No (mocked)   |
| `staging`    | Integration + DAST + staging gate | Merge to `main` (auto)            | Yes           |
| `production` | Live traffic                      | Manual approve after staging gate | Yes           |

Staging deploy is automatic on every `main` merge. Production deploy requires explicit
pipeline approval by the Tech Lead or SRE Lead after the staging gate passes.

---

## Kill-Switch Procedure (ADR-0025)

When the kill-switch is activated (automatically or manually):

```
1. Audit event `agent.kill_switch_activated` written (< 1s)
2. Vault AppRole secret_ids revoked (< 30s):
   - auth/approle/
   - secret/data/llm/
   - secret/data/hitl/
3. Pod terminated via sys.exit(1) (< 10s)
4. Kubernetes restarts pod — new secret_id required before agent resumes
5. On-call paged via PagerDuty (auto, from audit event)
```

RTO targets: pod termination < 10s, full credential revocation < 30s, total < 60s.

After kill-switch: manual investigation required before re-enabling automation.
New secret_ids issued only after root cause identified and mitigated.

---

## Hotfix Procedure

For P1 incidents requiring an emergency fix to production:

```
main
  └── hotfix/<issue>-<slug>
        ├── Fix committed
        ├── Minimal test added
        ├── PR opened against main
        ├── Fast-tracked CI (still must pass G04, G05, G10 at minimum)
        ├── 1 approval required
        └── Merge → deploy to production via hotfix pipeline
                  (bypasses staging gate with explicit approval from SRE Lead)
```

Post-hotfix: full staging gate run within 24 hours; post-mortem filed.
