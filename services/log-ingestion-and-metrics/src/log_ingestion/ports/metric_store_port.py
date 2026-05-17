"""Driven port: abstract interface for all metric persistence and query operations.

Defines the contract that RedisMetricAdapter (#64) must fulfil.
The domain and application layers depend only on this ABC — never on the concrete adapter.

References: ADR-0002 (hexagonal), ADR-0034 (Redis Sorted Sets), ADR-0035 (ZRANK percentile),
Spec LIM-01 §3.6 (storage layout), Spec LIM-02 §3.3–§3.5 (analytics read operations).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from log_ingestion.domain.models.metric import MetricPoint


class MetricStorePort(ABC):
    """Secondary (driven) port: persistence and query interface for Golden Signal metrics.

    All methods are async because the concrete adapter uses the asyncio redis-py client.
    Implementors must provide atomicity guarantees for store_batch() (single pipeline).
    """

    # ── write ──────────────────────────────────────────────────────────────────

    @abstractmethod
    async def store_batch(self, points: list[MetricPoint]) -> None:
        """Persist a batch of MetricPoints atomically in a single Redis pipeline.

        For each MetricPoint:
          - LATENCY  → ZADD  lim:lat:{backend}:{path}:{window_ts}  score=value  member=uuid
          - TRAFFIC  → INCR  lim:trx:{backend}:{path}:{window_ts}
          - ERROR    → INCR  lim:err4 or lim:err5 based on the originating status_code
          - SATURATION → INCR lim:sat:{backend}:{path}:{window_ts}  (only when value == 1.0)
        EXPIRE is refreshed for every key on every write (Spec LIM-01 §3.6, ADR-0030).

        Raises:
            MetricStoreError: if the pipeline execution fails.
        """

    # ── counter reads ──────────────────────────────────────────────────────────

    @abstractmethod
    async def get_counter(self, key: str) -> int:
        """Return the integer value of a Redis String counter, or 0 if absent."""

    # ── sorted-set reads (LATENCY) ─────────────────────────────────────────────

    @abstractmethod
    async def get_sorted_set_cardinality(self, key: str) -> int:
        """Return the number of members in a sorted set (ZCARD), or 0 if the key is absent."""

    @abstractmethod
    async def get_sorted_set_score_at_rank(self, key: str, rank: int) -> float:
        """Return the score of the member at the given 0-based rank (ZRANGE key rank rank WITHSCORES).

        Returns 0.0 if the key does not exist or the rank is out of bounds.
        """

    # ── multi-path aggregation (SCAN + ZUNIONSTORE) ────────────────────────────

    @abstractmethod
    async def scan_keys(self, pattern: str) -> list[str]:
        """Return all keys matching ``pattern`` via non-blocking SCAN iteration.

        Used to discover per-path keys when ``path`` is omitted from GET /analytics
        (Spec LIM-02 §3.5).
        """

    @abstractmethod
    async def union_sorted_sets_to_temp(self, dest_key: str, source_keys: list[str]) -> int:
        """Merge ``source_keys`` into ``dest_key`` with ZUNIONSTORE.

        Returns the cardinality of the resulting set.
        Used for multi-path latency aggregation (Spec LIM-02 §3.5).
        """

    @abstractmethod
    async def delete_key(self, key: str) -> None:
        """Delete a single key. Used to remove ZUNIONSTORE temporary keys after query."""

    # ── health ─────────────────────────────────────────────────────────────────

    @abstractmethod
    async def ping(self) -> bool:
        """Return True if the store responds to a PING within the health-check timeout.

        Used by GET /health/ready (Spec LIM-02 §3.8).
        """
