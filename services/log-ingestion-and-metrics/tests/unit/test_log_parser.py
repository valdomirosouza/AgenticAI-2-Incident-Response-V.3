"""Unit tests for LogParser domain service.

Covers Spec LIM-01 §3.2 (path extraction), §3.4 (Golden Signal extraction),
and §3.5 (window bucketing). All fixtures use the canonical schema from conftest.py.
No I/O — purely domain logic under test.
"""

from __future__ import annotations

from typing import Any

import pytest

from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry
from log_ingestion.domain.models.metric import SignalType
from log_ingestion.domain.services.log_parser import LogParser

_WINDOW = 300  # 5-minute window used throughout these tests


@pytest.fixture
def parser() -> LogParser:
    return LogParser(sat_threshold_ms=50)


@pytest.fixture
def points(parser: LogParser, haproxy_entry: HaproxyLogEntry) -> list:
    return parser.parse(haproxy_entry, _WINDOW)


# ── helpers ────────────────────────────────────────────────────────────────────


def _signal(points: list, signal: SignalType) -> float:
    return next(p.value for p in points if p.signal == signal)


# ── Traffic signal ─────────────────────────────────────────────────────────────


class TestTrafficSignal:
    def test_traffic_always_one(self, points: list) -> None:
        assert _signal(points, SignalType.TRAFFIC) == 1.0

    def test_traffic_backend_matches_entry(self, points: list) -> None:
        traffic = next(p for p in points if p.signal == SignalType.TRAFFIC)
        assert traffic.backend == "web-servers"


# ── Latency signal ─────────────────────────────────────────────────────────────


class TestLatencySignal:
    def test_latency_equals_total_time(self, points: list) -> None:
        # Spec LIM-01 §3.4: LATENCY value = timers.total_time (ms)
        assert _signal(points, SignalType.LATENCY) == 105.0

    def test_latency_zero_total_time(
        self, parser: LogParser, haproxy_entry_dict: dict[str, Any]
    ) -> None:
        haproxy_entry_dict["timers"]["total_time"] = 0
        entry = HaproxyLogEntry.model_validate(haproxy_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.LATENCY) == 0.0


# ── Error signal ───────────────────────────────────────────────────────────────


class TestErrorSignal:
    def test_clean_request_error_zero(self, points: list) -> None:
        # status_code=200, termination_state="--" → ERROR=0
        assert _signal(points, SignalType.ERROR) == 0.0

    def test_4xx_status_code_error_one(
        self, parser: LogParser, error_4xx_entry_dict: dict[str, Any]
    ) -> None:
        entry = HaproxyLogEntry.model_validate(error_4xx_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.ERROR) == 1.0

    def test_5xx_status_code_error_one(
        self, parser: LogParser, error_5xx_entry_dict: dict[str, Any]
    ) -> None:
        entry = HaproxyLogEntry.model_validate(error_5xx_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.ERROR) == 1.0

    def test_abnormal_termination_error_one_despite_200(
        self, parser: LogParser, abnormal_termination_entry_dict: dict[str, Any]
    ) -> None:
        # Spec LIM-01 §3.4: termination_state != "--" → ERROR=1 regardless of status_code
        entry = HaproxyLogEntry.model_validate(abnormal_termination_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.ERROR) == 1.0

    def test_boundary_status_400_is_error(
        self, parser: LogParser, haproxy_entry_dict: dict[str, Any]
    ) -> None:
        haproxy_entry_dict["status_code"] = 400
        entry = HaproxyLogEntry.model_validate(haproxy_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.ERROR) == 1.0

    def test_status_399_is_not_error(
        self, parser: LogParser, haproxy_entry_dict: dict[str, Any]
    ) -> None:
        haproxy_entry_dict["status_code"] = 399
        entry = HaproxyLogEntry.model_validate(haproxy_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.ERROR) == 0.0


# ── Saturation signal ──────────────────────────────────────────────────────────


class TestSaturationSignal:
    def test_low_wait_saturation_zero(self, points: list) -> None:
        # timers.wait=2 < threshold=50 → SATURATION=0
        assert _signal(points, SignalType.SATURATION) == 0.0

    def test_high_wait_saturation_one(
        self, parser: LogParser, high_wait_entry_dict: dict[str, Any]
    ) -> None:
        # Spec LIM-01 §3.4: timers.wait=80 > threshold=50 → SATURATION=1
        entry = HaproxyLogEntry.model_validate(high_wait_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.SATURATION) == 1.0

    def test_wait_exactly_at_threshold_is_not_saturated(
        self, parser: LogParser, haproxy_entry_dict: dict[str, Any]
    ) -> None:
        # Spec LIM-01 §3.4: condition is ">" not ">="
        haproxy_entry_dict["timers"]["wait"] = 50
        entry = HaproxyLogEntry.model_validate(haproxy_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert _signal(pts, SignalType.SATURATION) == 0.0

    def test_custom_threshold(self, haproxy_entry_dict: dict[str, Any]) -> None:
        custom_parser = LogParser(sat_threshold_ms=100)
        haproxy_entry_dict["timers"]["wait"] = 80
        entry = HaproxyLogEntry.model_validate(haproxy_entry_dict)
        pts = custom_parser.parse(entry, _WINDOW)
        # wait=80 < threshold=100 → not saturated
        assert _signal(pts, SignalType.SATURATION) == 0.0


# ── Path extraction ────────────────────────────────────────────────────────────


class TestPathExtraction:
    def test_simple_path_extracted(self, points: list) -> None:
        traffic = next(p for p in points if p.signal == SignalType.TRAFFIC)
        assert traffic.path == "/api/v1/data"

    def test_query_string_stripped(
        self, parser: LogParser, query_string_entry_dict: dict[str, Any]
    ) -> None:
        # Spec LIM-01 §3.2: 'POST /api/v1/users?dry_run=1 HTTP/1.1' → '/api/v1/users'
        entry = HaproxyLogEntry.model_validate(query_string_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        traffic = next(p for p in pts if p.signal == SignalType.TRAFFIC)
        assert traffic.path == "/api/v1/users"

    def test_delete_path_extracted(
        self, parser: LogParser, haproxy_entry_dict: dict[str, Any]
    ) -> None:
        haproxy_entry_dict["request"] = "DELETE /api/v1/items/42 HTTP/1.1"
        entry = HaproxyLogEntry.model_validate(haproxy_entry_dict)
        pts = parser.parse(entry, _WINDOW)
        assert next(p for p in pts if p.signal == SignalType.TRAFFIC).path == "/api/v1/items/42"


# ── Window bucketing ───────────────────────────────────────────────────────────


class TestWindowBucketing:
    def test_window_ts_is_floor_aligned(
        self, parser: LogParser, haproxy_entry: HaproxyLogEntry
    ) -> None:
        pts = parser.parse(haproxy_entry, _WINDOW)
        ts = next(p.window_ts for p in pts)
        assert ts % _WINDOW == 0

    def test_same_window_ts_for_all_signals(
        self, parser: LogParser, haproxy_entry: HaproxyLogEntry
    ) -> None:
        pts = parser.parse(haproxy_entry, _WINDOW)
        window_tss = {p.window_ts for p in pts}
        assert len(window_tss) == 1

    def test_1m_window(self, parser: LogParser, haproxy_entry: HaproxyLogEntry) -> None:
        pts = parser.parse(haproxy_entry, 60)
        ts = next(p.window_ts for p in pts)
        assert ts % 60 == 0

    def test_unsupported_window_raises(
        self, parser: LogParser, haproxy_entry: HaproxyLogEntry
    ) -> None:
        with pytest.raises(ValueError, match="window_seconds"):
            parser.parse(haproxy_entry, 120)


# ── Output shape ───────────────────────────────────────────────────────────────


class TestOutputShape:
    def test_parse_returns_exactly_four_points(self, points: list) -> None:
        assert len(points) == 4

    def test_all_four_signals_present(self, points: list) -> None:
        signals = {p.signal for p in points}
        assert signals == {
            SignalType.TRAFFIC,
            SignalType.ERROR,
            SignalType.LATENCY,
            SignalType.SATURATION,
        }

    def test_client_ip_not_in_any_point(
        self, parser: LogParser, haproxy_entry: HaproxyLogEntry
    ) -> None:
        # ADR-0028: client_ip must never appear in MetricPoints
        pts = parser.parse(haproxy_entry, _WINDOW)
        for pt in pts:
            assert not hasattr(pt, "client_ip")
