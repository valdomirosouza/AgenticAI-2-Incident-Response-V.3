"""Unit tests for IngestionService.

Verifies that IngestionService correctly orchestrates LogParser + MetricStorePort:
  - is a valid IngestionPort implementation
  - accumulates MetricPoints across all windows in a single store_batch call
  - skips store_batch when the entry list is empty
  - respects custom windows tuple
  - never forwards client_ip to the store (ADR-0028)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from log_ingestion.adapters.ingestion_service import IngestionService
from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry
from log_ingestion.domain.models.metric import MetricPoint, SignalType
from log_ingestion.domain.services.log_parser import LogParser
from log_ingestion.ports.ingestion_port import IngestionPort
from log_ingestion.ports.metric_store_port import MetricStorePort


# ── fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_store() -> MetricStorePort:
    store = MagicMock(spec=MetricStorePort)
    store.store_batch = AsyncMock()
    return store


@pytest.fixture
def service(mock_store: MetricStorePort) -> IngestionService:
    return IngestionService(store=mock_store)


# ── identity ───────────────────────────────────────────────────────────────────


class TestInit:
    def test_is_ingestion_port(self, service: IngestionService) -> None:
        assert isinstance(service, IngestionPort)

    def test_default_parser_created_when_none_given(
        self, mock_store: MetricStorePort
    ) -> None:
        svc = IngestionService(store=mock_store)
        assert svc._parser is not None
        assert isinstance(svc._parser, LogParser)

    def test_custom_parser_accepted(self, mock_store: MetricStorePort) -> None:
        custom_parser = LogParser(sat_threshold_ms=100)
        svc = IngestionService(store=mock_store, parser=custom_parser)
        assert svc._parser is custom_parser


# ── empty list ─────────────────────────────────────────────────────────────────


class TestEmptyBatch:
    @pytest.mark.asyncio
    async def test_empty_entries_skips_store(
        self, service: IngestionService, mock_store: MetricStorePort
    ) -> None:
        await service.ingest([])
        mock_store.store_batch.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_entries_no_error(self, service: IngestionService) -> None:
        await service.ingest([])  # must not raise


# ── MetricPoint accumulation ───────────────────────────────────────────────────


class TestMetricPointAccumulation:
    @pytest.mark.asyncio
    async def test_single_entry_one_window_four_points(
        self,
        service: IngestionService,
        mock_store: MetricStorePort,
        haproxy_entry: HaproxyLogEntry,
    ) -> None:
        await service.ingest([haproxy_entry], windows=(300,))
        points: list[MetricPoint] = mock_store.store_batch.call_args[0][0]
        assert len(points) == 4

    @pytest.mark.asyncio
    async def test_single_entry_four_windows_sixteen_points(
        self,
        service: IngestionService,
        mock_store: MetricStorePort,
        haproxy_entry: HaproxyLogEntry,
    ) -> None:
        await service.ingest([haproxy_entry], windows=(60, 300, 900, 3600))
        points: list[MetricPoint] = mock_store.store_batch.call_args[0][0]
        assert len(points) == 16  # 4 signals × 4 windows

    @pytest.mark.asyncio
    async def test_two_entries_one_window_eight_points(
        self,
        service: IngestionService,
        mock_store: MetricStorePort,
        haproxy_entry: HaproxyLogEntry,
    ) -> None:
        await service.ingest([haproxy_entry, haproxy_entry], windows=(300,))
        points: list[MetricPoint] = mock_store.store_batch.call_args[0][0]
        assert len(points) == 8  # 2 entries × 4 signals

    @pytest.mark.asyncio
    async def test_all_four_signal_types_present(
        self,
        service: IngestionService,
        mock_store: MetricStorePort,
        haproxy_entry: HaproxyLogEntry,
    ) -> None:
        await service.ingest([haproxy_entry], windows=(300,))
        points: list[MetricPoint] = mock_store.store_batch.call_args[0][0]
        signals = {p.signal for p in points}
        assert signals == {
            SignalType.TRAFFIC,
            SignalType.ERROR,
            SignalType.LATENCY,
            SignalType.SATURATION,
        }


# ── single store_batch call ────────────────────────────────────────────────────


class TestSingleStoreBatchCall:
    @pytest.mark.asyncio
    async def test_store_batch_called_exactly_once(
        self,
        service: IngestionService,
        mock_store: MetricStorePort,
        haproxy_entry: HaproxyLogEntry,
    ) -> None:
        await service.ingest([haproxy_entry, haproxy_entry], windows=(60, 300))
        assert mock_store.store_batch.await_count == 1

    @pytest.mark.asyncio
    async def test_custom_windows_respected(
        self,
        service: IngestionService,
        mock_store: MetricStorePort,
        haproxy_entry: HaproxyLogEntry,
    ) -> None:
        await service.ingest([haproxy_entry], windows=(60,))
        points: list[MetricPoint] = mock_store.store_batch.call_args[0][0]
        window_tss = {p.window_ts for p in points}
        # All points in the same 60-second window bucket
        assert len(window_tss) == 1
        assert next(iter(window_tss)) % 60 == 0


# ── PII boundary ───────────────────────────────────────────────────────────────


class TestPIIBoundary:
    @pytest.mark.asyncio
    async def test_no_point_has_client_ip_attribute(
        self,
        service: IngestionService,
        mock_store: MetricStorePort,
        haproxy_entry: HaproxyLogEntry,
    ) -> None:
        await service.ingest([haproxy_entry], windows=(300,))
        points: list[MetricPoint] = mock_store.store_batch.call_args[0][0]
        for point in points:
            assert not hasattr(point, "client_ip")
