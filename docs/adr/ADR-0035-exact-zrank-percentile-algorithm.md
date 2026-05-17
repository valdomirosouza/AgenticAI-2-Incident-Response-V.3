# ADR-0035: Exact ZRANK Percentile Algorithm via ZRANGE

**Status**: Accepted
**Date**: 2026-05-17
**Deciders**: Tech Lead, SRE Lead
**Affected RQs**: RQ1, RQ2

---

## Context

`GET /analytics` must return latency percentiles (default: p50, p95, p99) for a given
backend+path+window combination. The data source is the Redis Sorted Set defined in
ADR-0034. The choice is whether to compute percentiles **exactly** (reading the actual
rank-ordered value from the set) or **approximately** (using a probabilistic sketch).

Approximate algorithms (t-digest, DDSketch, HDR Histogram) achieve O(1) memory by
trading accuracy for scale. The trade-off is only worth accepting when:
(a) the dataset size is unbounded or extremely large, or
(b) exact computation is too slow for the required latency SLO.

Neither condition applies here: each window bucket holds at most the entries written
within a bounded TTL window (24 hours, ADR-0030), and `ZRANGE key rank rank` is
O(log N) — sub-millisecond for any realistic dataset size. Approximate results would
introduce non-determinism in `DetectionAgent` thresholds, complicating auditability
(EU AI Act Art. 12, NIST AI RMF GOVERN-1).

---

## Decision

Percentiles are computed **exactly** using the following algorithm against the
Redis Sorted Set `lim:lat:{backend}:{path}:{window_ts}`:

```python
import math

def query_percentile(redis, key: str, p: int) -> float:
    card = redis.zcard(key)                      # total entries in set
    if card == 0:
        return 0.0
    rank = math.ceil(p / 100 * card) - 1        # 0-based rank
    rank = max(0, min(rank, card - 1))           # clamp to [0, card-1]
    result = redis.zrange(key, rank, rank, withscores=True)
    return result[0][1] if result else 0.0
```

- `ZCARD` returns the total number of members in O(1).
- `math.ceil(p / 100 * card)` computes the nearest-rank index for percentile `p`.
- `ZRANGE key rank rank WITHSCORES` retrieves the single member at that 0-based rank in O(log N).
- The result is the exact score (latency in ms, stored as a float).

**Worked examples:**

| `ZCARD` | Percentile `p` | `rank = ceil(p/100 * card) - 1` | Interpretation       |
| ------- | -------------- | ------------------------------- | -------------------- |
| 1       | 99             | `ceil(0.99 × 1) − 1 = 0`        | Only entry returned  |
| 100     | 50             | `ceil(0.50 × 100) − 1 = 49`     | 50th-smallest value  |
| 100     | 99             | `ceil(0.99 × 100) − 1 = 98`     | 99th-smallest value  |
| 1 000   | 95             | `ceil(0.95 × 1000) − 1 = 949`   | 950th-smallest value |

Both `ZCARD` and `ZRANGE` are issued in the same Redis pipeline as the other
analytics reads to minimise round-trips.

---

## Alternatives Considered

| Alternative                               | Pros                                                           | Cons                                                                                                                           |
| ----------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| t-digest (Redis module or client library) | Sub-linear memory; industry standard for streaming percentiles | Approximate (error ≤ 1% but non-zero); requires extra library; non-deterministic for identical inputs; complicates audit trail |
| DDSketch (datadogpy or redis-py-cluster)  | Relative error guarantee                                       | Same approximation concern; supply-chain risk (ADR-0034); not in vanilla Redis                                                 |
| HDR Histogram (hdrh library, client-side) | Exact for integer latencies; compact                           | Requires fetching all sorted-set scores to client for reconstruction; defeats the purpose of Redis storage                     |
| ZRANGE full set + client sort             | No Redis module needed                                         | O(N) data transfer per query; unacceptable latency for large windows                                                           |
| ZRANGE rank rank (chosen)                 | O(log N); exact; deterministic; no extra library               | Requires one `ZCARD` + one `ZRANGE` per percentile; mitigated by pipeline batching                                             |

---

## Consequences

**Positive:**

- Results are deterministic and auditable: the same dataset always produces the same percentile value, satisfying EU AI Act Art. 12 (record-keeping) and NIST AI RMF GOVERN-1.
- No additional client libraries or Redis modules required.
- The `DetectionAgent` can rely on stable threshold comparisons (e.g., p99 > 200 ms triggers `incident.created`) without probabilistic drift.
- Unit tests can assert exact percentile values from fixture datasets (RULE-C02).

**Negative / Trade-offs:**

- Each distinct percentile value (p50, p95, p99) requires one `ZCARD` + one `ZRANGE` pipeline pair. For the default three percentiles this adds three pipeline calls per analytics request — negligible at research scale.
- If the Sorted Set grows beyond ~500 k members (pathological traffic spike with no TTL expiry working correctly), `ZRANGE` latency remains O(log N) but memory pressure increases. Mitigated by ADR-0030 TTL and the 1 000-entry batch cap on ingestion.

---

## Review Criteria

Revisit if: (a) p99 analytics query latency exceeds 10 ms under production load, indicating the O(log N) Redis cost is no longer acceptable and a sketch approach is warranted; or (b) the `DetectionAgent` SLO requires sub-millisecond percentile queries that Redis cannot satisfy, at which point an in-process HDR Histogram over a streaming window becomes the better option.

---

## References

- ADR-0030: Data-Retention TTL Policy (bounds max Sorted Set cardinality per window)
- ADR-0034: Redis Sorted Sets for Latency Distribution Storage (data structure this algorithm reads)
- Spec LIM-02 §3.4: Exact Percentile Calculation — `services/log-ingestion-and-metrics/specs/analytics-api.md`
- Dunning, T. & Ertl, O. (2019). _Computing Extremely Accurate Quantiles Using t-Digests_. arXiv:1902.04023. (considered and rejected)
- Redis documentation: [ZRANGE](https://redis.io/commands/zrange/), [ZCARD](https://redis.io/commands/zcard/)
- Issue [#60](https://github.com/valdomirosouza/AgenticAI-2-Incident-Response-V.3/issues/60)
