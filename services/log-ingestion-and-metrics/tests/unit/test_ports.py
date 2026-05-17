"""Unit tests for MetricStorePort, IngestionPort, and IngestionResult.

Verifies that:
  - Both ABCs enforce abstractmethod contracts (TypeError on direct instantiation).
  - Concrete stubs that implement all methods can be instantiated and called.
  - IngestionResult is immutable, validates invariants, and caps error list length.

No I/O — purely structural and invariant tests.
"""

from __future__ import annotations

import pytest

from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry
from log_ingestion.domain.models.metric import MetricPoint
from log_ingestion.ports.ingestion_port import IngestionPort, IngestionResult
from log_ingestion.ports.metric_store_port import MetricStorePort


# ── Stub implementations ───────────────────────────────────────────────────────


class _StubMetricStore(MetricStorePort):
    """Minimal in-memory stub that satisfies all abstract methods."""

    async def store_batch(self, points: list[MetricPoint]) -> None:
        pass

    async def get_counter(self, key: str) -> int:
        return 0

    async def get_sorted_set_cardinality(self, key: str) -> int:
        return 0

    async def get_sorted_set_score_at_rank(self, key: str, rank: int) -> float:
        return 0.0

    async def scan_keys(self, pattern: str) -> list[str]:
        return []

    async def union_sorted_sets_to_temp(self, dest_key: str, source_keys: list[str]) -> int:
        return 0

    async def delete_key(self, key: str) -> None:
        pass

    async def ping(self) -> bool:
        return True


class _StubIngestion(IngestionPort):
    """Minimal stub that satisfies the IngestionPort abstract method."""

    async def ingest(
        self,
        entries: list[HaproxyLogEntry],
        windows: tuple[int, ...] = (300,),
    ) -> None:
        pass


# ── MetricStorePort ────────────────────────────────────────────────────────────


class TestMetricStorePort:
    def test_cannot_instantiate_abc_directly(self) -> None:
        with pytest.raises(TypeError):
            MetricStorePort()  # type: ignore[abstract]

    def test_partial_implementation_raises(self) -> None:
        class _Partial(MetricStorePort):
            async def store_batch(self, points: list[MetricPoint]) -> None:
                pass
            # remaining abstract methods intentionally omitted

        with pytest.raises(TypeError):
            _Partial()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        store = _StubMetricStore()
        assert isinstance(store, MetricStorePort)

    @pytest.mark.asyncio
    async def test_store_batch_callable(self) -> None:
        store = _StubMetricStore()
        await store.store_batch([])  # must not raise

    @pytest.mark.asyncio
    async def test_get_counter_returns_int(self) -> None:
        store = _StubMetricStore()
        result = await store.get_counter("lim:trx:web-servers:/api:1718899200")
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_get_sorted_set_cardinality_returns_int(self) -> None:
        store = _StubMetricStore()
        result = await store.get_sorted_set_cardinality("lim:lat:web-servers:/api:1718899200")
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_get_sorted_set_score_at_rank_returns_float(self) -> None:
        store = _StubMetricStore()
        result = await store.get_sorted_set_score_at_rank("lim:lat:b:/p:0", 0)
        assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_scan_keys_returns_list(self) -> None:
        store = _StubMetricStore()
        result = await store.scan_keys("lim:trx:web-servers:*:1718899200")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_union_sorted_sets_returns_int(self) -> None:
        store = _StubMetricStore()
        result = await store.union_sorted_sets_to_temp("dest", ["src1", "src2"])
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_delete_key_callable(self) -> None:
        store = _StubMetricStore()
        await store.delete_key("some:key")  # must not raise

    @pytest.mark.asyncio
    async def test_ping_returns_bool(self) -> None:
        store = _StubMetricStore()
        result = await store.ping()
        assert isinstance(result, bool)
        assert result is True


# ── IngestionPort ──────────────────────────────────────────────────────────────


class TestIngestionPort:
    def test_cannot_instantiate_abc_directly(self) -> None:
        with pytest.raises(TypeError):
            IngestionPort()  # type: ignore[abstract]

    def test_full_implementation_instantiates(self) -> None:
        svc = _StubIngestion()
        assert isinstance(svc, IngestionPort)

    @pytest.mark.asyncio
    async def test_ingest_callable_with_empty_list(self) -> None:
        svc = _StubIngestion()
        await svc.ingest([])  # must not raise

    @pytest.mark.asyncio
    async def test_ingest_callable_with_custom_windows(self, haproxy_entry: HaproxyLogEntry) -> None:
        svc = _StubIngestion()
        await svc.ingest([haproxy_entry], windows=(60, 300))  # must not raise


# ── IngestionResult ────────────────────────────────────────────────────────────


class TestIngestionResult:
    def test_all_accepted(self) -> None:
        r = IngestionResult(accepted=3, rejected=0)
        assert r.accepted == 3
        assert r.rejected == 0
        assert r.errors == ()

    def test_partial_failure(self) -> None:
        r = IngestionResult(accepted=2, rejected=1, errors=("parse error on entry 0",))
        assert r.accepted == 2
        assert r.rejected == 1
        assert len(r.errors) == 1

    def test_is_immutable(self) -> None:
        r = IngestionResult(accepted=1, rejected=0)
        with pytest.raises((AttributeError, TypeError)):
            r.accepted = 5  # type: ignore[misc]

    def test_negative_accepted_raises(self) -> None:
        with pytest.raises(ValueError, match="accepted"):
            IngestionResult(accepted=-1, rejected=0)

    def test_negative_rejected_raises(self) -> None:
        with pytest.raises(ValueError, match="rejected"):
            IngestionResult(accepted=0, rejected=-1)

    def test_errors_capped_at_ten(self) -> None:
        with pytest.raises(ValueError, match="errors"):
            IngestionResult(accepted=0, rejected=11, errors=tuple(f"e{i}" for i in range(11)))

    def test_exactly_ten_errors_accepted(self) -> None:
        r = IngestionResult(accepted=0, rejected=10, errors=tuple(f"e{i}" for i in range(10)))
        assert len(r.errors) == 10

    def test_zero_counts_valid(self) -> None:
        r = IngestionResult(accepted=0, rejected=0)
        assert r.accepted == 0
        assert r.rejected == 0
