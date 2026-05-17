# ADR-0030: Data Retention Policy with Explicit TTL per Data Category

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Valdomiro de Oliveira Souza Júnior (Tech Lead / DPO / Privacy Lead — researcher)
**Affected RQs**: RQ4 (privacy compliance)

---

## Context

LGPD art. 16 and GDPR art. 5(1)(e) (storage limitation principle) require that personal
data is kept only as long as necessary for the purpose for which it was collected.
Indefinite retention of observability data, audit logs and incident post-mortems that
contain PII (even pseudonymised) is non-compliant.

The system produces several data categories with different retention needs:

- **Hot observability data** (logs, traces, metrics) — queried frequently during active
  incidents; old data rarely needed; high storage cost if retained indefinitely.
- **Audit trail** — needed for compliance evidence and post-mortem reconstruction;
  must be retained for regulatory periods.
- **Research corpus** — anonymised incident datasets used for dissertation evaluation;
  retention tied to academic purpose.
- **LLM prompt/response cache** — if retained, constitutes personal data processing;
  must be strictly limited.

Without explicit TTLs and automated deletion, retention defaults to indefinite —
a clear LGPD/GDPR violation and an increasing storage cost.

## Decision

Every data category produced by the system has an **explicit TTL with automated
deletion**. Manual deletion is not sufficient — the system must enforce TTL
programmatically.

### Data retention schedule

| Data category                          | Hot TTL                  | Cold archive TTL                   | Total max retention        | Deletion method                                     | Personal data?                   |
| -------------------------------------- | ------------------------ | ---------------------------------- | -------------------------- | --------------------------------------------------- | -------------------------------- |
| **Application logs** (structured JSON) | 30 days                  | 60 days                            | 90 days                    | Log backend TTL (Loki / Cloud Logging)              | Yes — pseudonymised `user_id`    |
| **Distributed traces**                 | 14 days                  | —                                  | 14 days                    | Jaeger / Tempo TTL                                  | Yes — `user_id`, span attributes |
| **Metrics time series**                | 15 days (raw)            | 1 year (downsampled 1m resolution) | 1 year                     | Prometheus retention + recording rules              | No (aggregated)                  |
| **Audit trail records**                | —                        | —                                  | 2 years minimum            | Append-only; TTL after 2 years via object lifecycle | Yes — pseudonymised role IDs     |
| **Incident post-mortems**              | Active + 90 days         | —                                  | 90 days post-close         | Automated archival + delete job                     | Yes — pseudonymised role labels  |
| **LLM prompt/response cache**          | Do not retain            | —                                  | Session only (in-memory)   | Never persisted to disk                             | Yes — may contain residual PII   |
| **Research corpus (anonymised)**       | Duration of dissertation | —                                  | Dissertation end + 5 years | Manual secure deletion per PRIVACY.md               | No (anonymised per ADR-0031)     |
| **Research corpus (pseudonymised)**    | Duration of dissertation | —                                  | Dissertation end only      | Automated deletion after thesis defence             | Yes — pseudonymised              |
| **SBOM / build artifacts**             | 90 days (PR gate)        | Life of release + 2 years          | Release + 2 years          | GitHub Actions artifact TTL + release cleanup       | No                               |
| **DPIA/RIPD document**                 | —                        | —                                  | Indefinite (legal record)  | Manual; requires DPO approval to delete             | No (no PII in doc itself)        |

### LLM prompt retention policy

LLM prompts and responses are **never persisted to disk or any storage backend**.
They exist only in process memory for the duration of the API call. Any caching of
LLM outputs (for latency reduction) is prohibited without a separate ADR documenting
the legal basis and TTL.

The `LLMAdapter` must not log the full prompt content — only the sanitized metadata
(token count, model, duration) is logged to the audit trail (ADR-0024).

### Automated deletion enforcement

| Backend                | TTL mechanism                                    |
| ---------------------- | ------------------------------------------------ |
| Loki                   | `retention_period: 90d` in Loki config           |
| Jaeger / Tempo         | `--es.max-span-age=336h` (14 days)               |
| Prometheus             | `--storage.tsdb.retention.time=15d`              |
| GCS / S3 (audit trail) | Object lifecycle rule: delete objects > 730 days |
| GitHub Actions         | `retention-days: 90` in workflow YAML            |

TTL configuration is version-controlled in `infrastructure/` and validated by the
Checkov IaC gate (ADR-0017 / ADR-0007 G02).

### Data subject deletion requests

LGPD art. 18 and GDPR art. 17 grant data subjects the right to erasure. For this
research project, deletion requests are handled manually within 15 days (LGPD art. 19)
by the DPO. The process:

1. Identify `user_id` to delete across all data categories.
2. Delete or anonymise all records containing that `user_id` from logs, traces and
   post-mortems within the retention window.
3. Audit trail records referencing that `user_id` cannot be deleted (append-only,
   ADR-0024) — they are anonymised in-place by replacing `user_id` with `[DELETED]`.
4. Confirm deletion in writing to the data subject within 15 days.

## Alternatives Considered

| Alternative                                              | Pros                                                                | Cons                                                                                          |
| -------------------------------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Indefinite retention**                                 | Zero effort; data always available                                  | LGPD art. 16 / GDPR art. 5(1)(e) violated; storage cost grows unbounded                       |
| **Manual deletion on request only**                      | Minimal tooling                                                     | Non-compliant — GDPR art. 5(1)(e) requires storage limitation by default, not only on request |
| **Explicit TTL per category with automated deletion** ✅ | LGPD/GDPR compliant; storage costs bounded; automated and auditable | Requires TTL configuration in each backend — one-time setup cost                              |

## Consequences

**Positive:**

- LGPD art. 16 and GDPR art. 5(1)(e) satisfied: every data category has a documented,
  automated TTL.
- Storage costs bounded — no unbounded accumulation of observability data.
- LLM prompt non-retention policy eliminates the highest-risk persistent PII exposure.

**Negative / Trade-offs:**

- 90-day log retention may be insufficient for long-running post-mortem investigations —
  post-mortems must be drafted within 90 days of incident close, which is the expected
  standard anyway.
- Audit trail 2-year retention with object lock means approximately 2GB/year of storage
  at projected incident volume — acceptable cost.

## Review Criteria

Revisit this decision if:

- A regulatory requirement (SOC 2 audit, ANPD inquiry) requires longer log retention
  than 90 days — extend the cold archive TTL and document the legal basis.
- Incident volume significantly exceeds projections — evaluate compressed archive tier
  for logs between 30 and 90 days.

## References

- LGPD (Lei 13.709/2018) Art. 16 — Data retention and deletion requirements
- LGPD Art. 18, 19 — Data subject rights and response timeline
- GDPR (EU 2016/679) Art. 5(1)(e) — Storage limitation principle
- GDPR Art. 17 — Right to erasure
- `docs/adr/ADR-0024-immutable-agent-audit-trail.md` — audit trail 2-year retention
- `docs/adr/ADR-0031-anonymization-standard-agent-datasets.md` — research corpus anonymization
- `PRIVACY.md` — public retention schedule
