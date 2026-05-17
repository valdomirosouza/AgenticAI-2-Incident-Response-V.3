"""Concrete Redis adapter implementing MetricStorePort.

Uses the asyncio redis-py client. All writes within store_batch are issued in a single
pipeline for atomicity (Spec LIM-01 §3.6, ADR-0034). TTLs are refreshed unconditionally
on every write (ADR-0030). Key segments are URL-encoded to prevent colon-injection via
crafted backend or path values (Spec LIM-01 §3.6).

Error class encoding convention (established by LogParser):
  - MetricPoint.value == 0.0 → clean request — no error key written
  - MetricPoint.value == 4.0 → 4xx error   — INCR lim:err4:{backend}:{path}:{window_ts}
  - MetricPoint.value == 5.0 → 5xx / abnormal termination → INCR lim:err5:{…}

References: ADR-0002 (hexagonal), ADR-0030 (TTLs), ADR-0034 (sorted sets),
ADR-0035 (ZRANK percentile), Spec LIM-01 §3.6, Spec LIM-02 §3.3–§3.5.
"""

from __future__ import annotations

import uuid
from urllib.parse import quote

import redis.asyncio as aioredis

from log_ingestion.domain.models.exceptions import MetricStoreError
from log_ingestion.domain.models.metric import MetricPoint, SignalType
from log_ingestion.ports.metric_store_port import MetricStorePort

_LAT_TTL: int = 86_400   # 24 h — latency sorted sets (ADR-0030)
_CTR_TTL: int = 604_800  # 7 d  — string counters    (ADR-0030)


def _seg(value: str) -> str:
    """URL-encode a Redis key segment to prevent colon-injection (Spec LIM-01 §3.6)."""
    return quote(value, safe="")


class RedisMetricAdapter(MetricStorePort):
    """MetricStorePort backed by a redis-py asyncio client.

    The adapter does not manage the Redis connection lifecycle; callers are responsible
    for creating and closing the ``redis.asyncio.Redis`` instance.
    """

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    # ── write ──────────────────────────────────────────────────────────────────

    async def store_batch(self, points: list[MetricPoint]) -> None:
        """Persist all MetricPoints in a single atomic Redis pipeline (Spec LIM-01 §3.6).

        Signal routing:
          - LATENCY    → ZADD lim:lat:{b}:{p}:{w}  score=value  member=uuid4 ; EXPIRE _LAT_TTL
          - TRAFFIC    → INCR lim:trx:{b}:{p}:{w}                            ; EXPIRE _CTR_TTL
          - ERROR 4xx  → INCR lim:err4:{b}:{p}:{w}  (value==4.0)            ; EXPIRE _CTR_TTL
          - ERROR 5xx  → INCR lim:err5:{b}:{p}:{w}  (value==5.0)            ; EXPIRE _CTR_TTL
          - SATURATION → INCR lim:sat:{b}:{p}:{w}   (only when value==1.0)  ; EXPIRE _CTR_TTL

        Raises:
            MetricStoreError: if the pipeline execute() call raises a RedisError.
        """
        async with self._redis.pipeline(transaction=True) as pipe:
            for point in points:
                b = _seg(point.backend)
                p = _seg(point.path)
                w = point.window_ts

                match point.signal:
                    case SignalType.LATENCY:
                        key = f"lim:lat:{b}:{p}:{w}"
                        pipe.zadd(key, {str(uuid.uuid4()): point.value})
                        pipe.expire(key, _LAT_TTL)

                    case SignalType.TRAFFIC:
                        key = f"lim:trx:{b}:{p}:{w}"
                        pipe.incr(key)
                        pipe.expire(key, _CTR_TTL)

                    case SignalType.ERROR:
                        if point.value == 0.0:
                            continue
                        prefix = "err4" if int(point.value) == 4 else "err5"
                        key = f"lim:{prefix}:{b}:{p}:{w}"
                        pipe.incr(key)
                        pipe.expire(key, _CTR_TTL)

                    case SignalType.SATURATION:
                        if point.value == 0.0:
                            continue
                        key = f"lim:sat:{b}:{p}:{w}"
                        pipe.incr(key)
                        pipe.expire(key, _CTR_TTL)

            try:
                await pipe.execute()
            except aioredis.RedisError as exc:
                raise MetricStoreError(str(exc)) from exc

    # ── counter reads ──────────────────────────────────────────────────────────

    async def get_counter(self, key: str) -> int:
        """Return the integer value of a Redis String counter, or 0 if the key is absent."""
        val = await self._redis.get(key)
        return int(val) if val is not None else 0

    # ── sorted-set reads ───────────────────────────────────────────────────────

    async def get_sorted_set_cardinality(self, key: str) -> int:
        """Return ZCARD of the key, or 0 if absent."""
        return await self._redis.zcard(key)

    async def get_sorted_set_score_at_rank(self, key: str, rank: int) -> float:
        """Return the score of the member at 0-based ``rank`` via ZRANGE … WITHSCORES.

        Returns 0.0 if the key does not exist or ``rank`` is out of bounds.
        """
        result = await self._redis.zrange(key, rank, rank, withscores=True)
        return float(result[0][1]) if result else 0.0

    # ── multi-path aggregation ─────────────────────────────────────────────────

    async def scan_keys(self, pattern: str) -> list[str]:
        """Return all keys matching ``pattern`` via non-blocking SCAN iteration."""
        keys: list[str] = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key if isinstance(key, str) else key.decode())
        return keys

    async def union_sorted_sets_to_temp(self, dest_key: str, source_keys: list[str]) -> int:
        """ZUNIONSTORE ``source_keys`` into ``dest_key``; return resulting cardinality."""
        return await self._redis.zunionstore(dest_key, source_keys)

    async def delete_key(self, key: str) -> None:
        """DELETE a single key. Used to remove ZUNIONSTORE temporary keys after query."""
        await self._redis.delete(key)

    # ── health ─────────────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        """Return True if Redis responds to PING; False on any RedisError."""
        try:
            return bool(await self._redis.ping())
        except aioredis.RedisError:
            return False
