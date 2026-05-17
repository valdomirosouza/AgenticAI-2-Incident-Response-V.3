# ADR-0034: Redis Sorted Sets for Latency Distribution Storage

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Tech Lead, SRE Lead
**Affected RQs**: RQ1, RQ2

---

## Context

The LIM service must persist individual latency samples (`timers.total_time` in ms)
per `backend + path + window_ts` bucket so that `GET /analytics` can return exact
percentile values (p50, p95, p99). The window buckets expire after 24 hours (ADR-0030).

Within each time window a given backend+path combination may accumulate up to tens of
thousands of individual request latency values. The storage structure must support:

1. Efficient **write** of individual samples during `POST /ingestion` batch processing.
2. Efficient **rank-based read** to retrieve the value at an arbitrary percentile rank.
3. Automatic **expiry** via Redis TTL so no background cleanup job is required.
4. **Single Redis instance** as the only external dependency (no additional services).

Three storage strategies were evaluated: (a) Redis List with client-side sorting,
(b) probabilistic sketch (t-digest or HLL) via a Redis module, and
(c) Redis Sorted Set with `ZADD score=latency_ms member=uuid`.

---

## Decision

Latency samples are stored in a **Redis Sorted Set** with:

- **Key pattern:** `lim:lat:{backend}:{path}:{window_ts}`
- **Score:** `timers.total_time` (integer milliseconds)
- **Member:** UUID v4 (guarantees uniqueness; prevents duplicate members collapsing scores)
- **TTL:** 86400 seconds (24 hours) per ADR-0030, refreshed on every `ZADD`

Write operation per log entry:

```
ZADD lim:lat:{backend}:{path}:{window_ts} {total_time} {uuid}
EXPIRE lim:lat:{backend}:{path}:{window_ts} 86400
```

Both commands are issued inside the same Redis pipeline (single round-trip per batch).

The Sorted Set data structure orders members by score automatically. This makes
rank-based retrieval (`ZRANGE key rank rank WITHSCORES`) an O(log N) operation
without any client-side sort, which is the foundation of the exact percentile
algorithm in ADR-0035.

---

## Alternatives Considered

| Alternative                        | Pros                                                           | Cons                                                                                                                                                          |
| ---------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Redis List (RPUSH + client sort)   | Simple write path                                              | Client-side sort O(N log N) per query; all data loaded into memory; impractical for large windows                                                             |
| Redis Stream + client aggregation  | Native time-series semantics                                   | Requires client-side sort per query; no rank primitive; larger memory footprint per entry                                                                     |
| t-digest / DDSketch (Redis module) | Sub-linear memory; accurate approximations                     | Requires `RedisBloom` or `redis-py-cluster` module; not in vanilla Redis; adds supply-chain risk (ADR-0002, devsecops/supply-chain.md); result is approximate |
| Redis Sorted Set (chosen)          | O(log N) rank query; exact result; native TTL; no extra module | Memory grows linearly with sample count — bounded by window TTL and batch limit (max 1000/call)                                                               |

---

## Consequences

**Positive:**

- `ZRANGE key rank rank WITHSCORES` returns the exact value at the computed rank in O(log N), enabling the exact percentile algorithm (ADR-0035).
- No additional Redis modules required; compatible with vanilla Redis 7.x and AWS ElastiCache.
- TTL expiry is automatic; no background cleanup job, no data accumulation beyond 24 hours.
- UUID members prevent silent score deduplication when two requests have identical latency.

**Negative / Trade-offs:**

- Memory usage is O(N) per window bucket. At max throughput (1 000 entries/call, multiple clients), a busy backend+path can accumulate large sets. Mitigated by: (a) 24-hour TTL hard limit, (b) each member is ~50 bytes (UUID string + float score + Redis overhead), making a 100 k-entry set ≈ 5 MB — acceptable for a research-scale deployment.
- `ZADD` with a UUID member does not deduplicate identical latency values; this is intentional (we want the full distribution, not unique values).

---

## Review Criteria

Revisit if: (a) observed memory usage per bucket exceeds 20 MB in production monitoring, indicating the need for reservoir sampling or sketch compression; or (b) the deployment target changes to a Redis environment that supports `RedisBloom` natively without supply-chain concerns.

---

## References

- ADR-0002: Hexagonal Architecture (RedisMetricAdapter as the port implementation)
- ADR-0030: Data-Retention TTL Policy (24-hour TTL for latency keys)
- ADR-0035: Exact ZRANK Percentile Algorithm (consumer of this storage layout)
- Spec LIM-01 §3.6: Redis Storage Layout — `services/log-ingestion-and-metrics/specs/log-ingestion-api.md`
- Redis documentation: [Sorted Sets](https://redis.io/docs/data-types/sorted-sets/)
- Issue [#60](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/60)
