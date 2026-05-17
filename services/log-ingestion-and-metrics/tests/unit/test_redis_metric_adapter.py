"""Unit tests for RedisMetricAdapter.

Uses fakeredis.FakeAsyncRedis as an in-process Redis substitute so tests run without
any network I/O. Each test gets an isolated FakeAsyncRedis instance via the ``redis``
fixture, ensuring no state leaks between cases.

Covers:
  - store_batch routing for all four Golden Signals (LATENCY, TRAFFIC, ERROR, SATURATION)
  - Error class encoding (4.0 → err4, 5.0 → err5, 0.0 → no write)
  - Saturation skip when value==0.0
  - TTL assertions for latency (86400 s) and counter (604800 s) keys
  - Key sanitisation — colons in backend/path are URL-encoded
  - get_counter, get_sorted_set_cardinality, get_sorted_set_score_at_rank
  - scan_keys, union_sorted_sets_to_temp, delete_key
  - ping (success and failure paths)
  - MetricStoreError raised on pipeline failure
  - isinstance check: adapter is a MetricStorePort
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis.aioredis
import pytest
import redis.asyncio as aioredis

from log_ingestion.adapters.redis_metric_adapter import RedisMetricAdapter
from log_ingestion.domain.models.exceptions import MetricStoreError
from log_ingestion.domain.models.metric import MetricPoint, SignalType
from log_ingestion.ports.metric_store_port import MetricStorePort

_BACKEND = "web-servers"
_PATH = "/api/v1/orders"
_WINDOW_TS = 1_718_899_200  # 2024-06-20T16:00:00 UTC (5-minute floor)


# ── fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
async def redis() -> fakeredis.aioredis.FakeRedis:
    r = fakeredis.aioredis.FakeRedis()
    yield r
    await r.aclose()


@pytest.fixture
def adapter(redis: fakeredis.aioredis.FakeRedis) -> RedisMetricAdapter:
    return RedisMetricAdapter(redis)


def _point(signal: SignalType, value: float) -> MetricPoint:
    return MetricPoint(
        signal=signal,
        value=value,
        backend=_BACKEND,
        path=_PATH,
        window_ts=_WINDOW_TS,
    )


def _trx_key() -> str:
    from urllib.parse import quote
    return f"lim:trx:{quote(_BACKEND, safe='')}:{quote(_PATH, safe='')}:{_WINDOW_TS}"


def _lat_key() -> str:
    from urllib.parse import quote
    return f"lim:lat:{quote(_BACKEND, safe='')}:{quote(_PATH, safe='')}:{_WINDOW_TS}"


def _err4_key() -> str:
    from urllib.parse import quote
    return f"lim:err4:{quote(_BACKEND, safe='')}:{quote(_PATH, safe='')}:{_WINDOW_TS}"


def _err5_key() -> str:
    from urllib.parse import quote
    return f"lim:err5:{quote(_BACKEND, safe='')}:{quote(_PATH, safe='')}:{_WINDOW_TS}"


def _sat_key() -> str:
    from urllib.parse import quote
    return f"lim:sat:{quote(_BACKEND, safe='')}:{quote(_PATH, safe='')}:{_WINDOW_TS}"


# ── init ───────────────────────────────────────────────────────────────────────


class TestInit:
    def test_is_metric_store_port(self, adapter: RedisMetricAdapter) -> None:
        assert isinstance(adapter, MetricStorePort)


# ── store_batch: TRAFFIC ───────────────────────────────────────────────────────


class TestStoreBatchTraffic:
    @pytest.mark.asyncio
    async def test_traffic_increments_trx_counter(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.TRAFFIC, 1.0)])
        assert await redis.get(_trx_key()) == b"1"

    @pytest.mark.asyncio
    async def test_traffic_two_points_counter_equals_two(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.TRAFFIC, 1.0)])
        await adapter.store_batch([_point(SignalType.TRAFFIC, 1.0)])
        assert await redis.get(_trx_key()) == b"2"

    @pytest.mark.asyncio
    async def test_traffic_sets_counter_ttl(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.TRAFFIC, 1.0)])
        ttl = await redis.ttl(_trx_key())
        assert 604_790 <= ttl <= 604_800


# ── store_batch: LATENCY ───────────────────────────────────────────────────────


class TestStoreBatchLatency:
    @pytest.mark.asyncio
    async def test_latency_adds_one_member_to_sorted_set(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.LATENCY, 105.0)])
        assert await redis.zcard(_lat_key()) == 1

    @pytest.mark.asyncio
    async def test_latency_two_entries_cardinality_two(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.LATENCY, 105.0)])
        await adapter.store_batch([_point(SignalType.LATENCY, 200.0)])
        assert await redis.zcard(_lat_key()) == 2

    @pytest.mark.asyncio
    async def test_latency_score_matches_value(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.LATENCY, 105.0)])
        result = await redis.zrange(_lat_key(), 0, 0, withscores=True)
        assert result[0][1] == pytest.approx(105.0)

    @pytest.mark.asyncio
    async def test_latency_sets_sorted_set_ttl(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.LATENCY, 105.0)])
        ttl = await redis.ttl(_lat_key())
        assert 86_390 <= ttl <= 86_400


# ── store_batch: ERROR ─────────────────────────────────────────────────────────


class TestStoreBatchError:
    @pytest.mark.asyncio
    async def test_error_4xx_increments_err4_key(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.ERROR, 4.0)])
        assert await redis.get(_err4_key()) == b"1"

    @pytest.mark.asyncio
    async def test_error_5xx_increments_err5_key(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.ERROR, 5.0)])
        assert await redis.get(_err5_key()) == b"1"

    @pytest.mark.asyncio
    async def test_error_zero_writes_no_error_key(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.ERROR, 0.0)])
        assert await redis.get(_err4_key()) is None
        assert await redis.get(_err5_key()) is None

    @pytest.mark.asyncio
    async def test_error_4xx_does_not_write_err5(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.ERROR, 4.0)])
        assert await redis.get(_err5_key()) is None

    @pytest.mark.asyncio
    async def test_error_5xx_does_not_write_err4(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.ERROR, 5.0)])
        assert await redis.get(_err4_key()) is None

    @pytest.mark.asyncio
    async def test_error_4xx_sets_counter_ttl(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.ERROR, 4.0)])
        ttl = await redis.ttl(_err4_key())
        assert 604_790 <= ttl <= 604_800


# ── store_batch: SATURATION ────────────────────────────────────────────────────


class TestStoreBatchSaturation:
    @pytest.mark.asyncio
    async def test_saturation_one_increments_sat_counter(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.SATURATION, 1.0)])
        assert await redis.get(_sat_key()) == b"1"

    @pytest.mark.asyncio
    async def test_saturation_zero_writes_no_sat_key(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await adapter.store_batch([_point(SignalType.SATURATION, 0.0)])
        assert await redis.get(_sat_key()) is None


# ── store_batch: empty and multi-signal ────────────────────────────────────────


class TestStoreBatchMisc:
    @pytest.mark.asyncio
    async def test_empty_batch_no_error(self, adapter: RedisMetricAdapter) -> None:
        await adapter.store_batch([])  # must not raise

    @pytest.mark.asyncio
    async def test_pipeline_failure_raises_metric_store_error(
        self, adapter: RedisMetricAdapter
    ) -> None:
        broken_pipe = AsyncMock()
        broken_pipe.__aenter__ = AsyncMock(return_value=broken_pipe)
        broken_pipe.__aexit__ = AsyncMock(return_value=False)
        broken_pipe.zadd = MagicMock()
        broken_pipe.incr = MagicMock()
        broken_pipe.expire = MagicMock()
        broken_pipe.execute = AsyncMock(
            side_effect=aioredis.RedisError("connection refused")
        )
        with patch.object(adapter._redis, "pipeline", return_value=broken_pipe):
            with pytest.raises(MetricStoreError, match="connection refused"):
                await adapter.store_batch([_point(SignalType.TRAFFIC, 1.0)])


# ── key sanitisation ───────────────────────────────────────────────────────────


class TestKeySanitisation:
    @pytest.mark.asyncio
    async def test_backend_colon_is_url_encoded(
        self, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        adapter = RedisMetricAdapter(redis)
        point = MetricPoint(
            signal=SignalType.TRAFFIC,
            value=1.0,
            backend="web:servers",  # colon must be encoded
            path="/api",
            window_ts=_WINDOW_TS,
        )
        await adapter.store_batch([point])
        # The key must contain "%3A" (URL-encoded colon), not a bare ":"
        keys = await redis.keys("lim:trx:*")
        assert len(keys) == 1
        key_str = keys[0].decode() if isinstance(keys[0], bytes) else keys[0]
        assert "%3A" in key_str


# ── get_counter ────────────────────────────────────────────────────────────────


class TestGetCounter:
    @pytest.mark.asyncio
    async def test_absent_key_returns_zero(self, adapter: RedisMetricAdapter) -> None:
        result = await adapter.get_counter("lim:trx:missing:key:0")
        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_stored_counter_value(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await redis.set(_trx_key(), 42)
        result = await adapter.get_counter(_trx_key())
        assert result == 42


# ── get_sorted_set_cardinality ─────────────────────────────────────────────────


class TestGetSortedSetCardinality:
    @pytest.mark.asyncio
    async def test_absent_key_returns_zero(self, adapter: RedisMetricAdapter) -> None:
        result = await adapter.get_sorted_set_cardinality("lim:lat:missing:key:0")
        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_cardinality_after_zadd(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await redis.zadd(_lat_key(), {"m1": 105.0, "m2": 200.0})
        result = await adapter.get_sorted_set_cardinality(_lat_key())
        assert result == 2


# ── get_sorted_set_score_at_rank ───────────────────────────────────────────────


class TestGetSortedSetScoreAtRank:
    @pytest.mark.asyncio
    async def test_absent_key_returns_zero(self, adapter: RedisMetricAdapter) -> None:
        result = await adapter.get_sorted_set_score_at_rank("lim:lat:missing:key:0", 0)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_returns_correct_score_at_rank_zero(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        # sorted set: [48.0, 512.0] → rank 0 → 48.0
        await redis.zadd(_lat_key(), {"a": 48.0, "b": 512.0})
        result = await adapter.get_sorted_set_score_at_rank(_lat_key(), 0)
        assert result == pytest.approx(48.0)

    @pytest.mark.asyncio
    async def test_returns_correct_score_at_rank_one(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        # sorted set: [48.0, 512.0] → rank 1 → 512.0
        await redis.zadd(_lat_key(), {"a": 48.0, "b": 512.0})
        result = await adapter.get_sorted_set_score_at_rank(_lat_key(), 1)
        assert result == pytest.approx(512.0)


# ── scan_keys ──────────────────────────────────────────────────────────────────


class TestScanKeys:
    @pytest.mark.asyncio
    async def test_no_matching_keys_returns_empty(self, adapter: RedisMetricAdapter) -> None:
        result = await adapter.scan_keys("lim:trx:nonexistent:*")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_matching_keys(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await redis.set("lim:trx:web-servers:%2Fapi:1000", 1)
        await redis.set("lim:trx:web-servers:%2Fapi:2000", 1)
        await redis.set("lim:trx:other:%2Fapi:1000", 1)
        result = await adapter.scan_keys("lim:trx:web-servers:*")
        assert len(result) == 2


# ── union_sorted_sets_to_temp + delete_key ─────────────────────────────────────


class TestUnionAndDelete:
    @pytest.mark.asyncio
    async def test_union_returns_merged_cardinality(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await redis.zadd("lim:lat:b:%2Fa:1000", {"x": 100.0})
        await redis.zadd("lim:lat:b:%2Fb:1000", {"y": 200.0, "z": 300.0})
        card = await adapter.union_sorted_sets_to_temp(
            "lim:lat:tmp:merged", ["lim:lat:b:%2Fa:1000", "lim:lat:b:%2Fb:1000"]
        )
        assert card == 3

    @pytest.mark.asyncio
    async def test_delete_key_removes_key(
        self, adapter: RedisMetricAdapter, redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await redis.set("lim:tmp:key", "value")
        await adapter.delete_key("lim:tmp:key")
        assert await redis.get("lim:tmp:key") is None


# ── ping ───────────────────────────────────────────────────────────────────────


class TestPing:
    @pytest.mark.asyncio
    async def test_ping_returns_true_when_redis_available(
        self, adapter: RedisMetricAdapter
    ) -> None:
        result = await adapter.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_ping_returns_false_on_redis_error(
        self, adapter: RedisMetricAdapter
    ) -> None:
        with patch.object(
            adapter._redis,
            "ping",
            side_effect=aioredis.RedisError("unreachable"),
        ):
            result = await adapter.ping()
        assert result is False
