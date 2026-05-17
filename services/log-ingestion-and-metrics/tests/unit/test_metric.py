"""Unit tests for MetricPoint, SignalType, AnalyticsResult and sub-models.

Covers Spec LIM-01 §3.4 (Golden Signal extraction model) and Spec LIM-02 §3.2
(analytics response schema). No I/O or Redis interaction.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from log_ingestion.domain.models.metric import (
    AnalyticsResult,
    ErrorMetric,
    MetricPoint,
    SaturationMetric,
    SignalType,
    TrafficMetric,
)


class TestSignalType:
    def test_all_four_golden_signals_defined(self) -> None:
        assert SignalType.TRAFFIC == "traffic"
        assert SignalType.ERROR == "error"
        assert SignalType.LATENCY == "latency"
        assert SignalType.SATURATION == "saturation"

    def test_signal_type_is_string(self) -> None:
        assert isinstance(SignalType.TRAFFIC, str)


class TestMetricPoint:
    def test_traffic_metric_point(self) -> None:
        mp = MetricPoint(
            signal=SignalType.TRAFFIC,
            value=1.0,
            backend="web-servers",
            path="/api/v1/data",
            window_ts=1_718_899_200,
        )
        assert mp.signal == SignalType.TRAFFIC
        assert mp.value == 1.0
        assert mp.backend == "web-servers"
        assert mp.path == "/api/v1/data"
        assert mp.window_ts == 1_718_899_200

    def test_latency_metric_point_stores_ms_value(self) -> None:
        mp = MetricPoint(
            signal=SignalType.LATENCY,
            value=105.0,
            backend="web-servers",
            path="/api/v1/data",
            window_ts=1_718_899_200,
        )
        assert mp.value == 105.0

    def test_saturation_metric_point_binary_value(self) -> None:
        mp_high = MetricPoint(
            signal=SignalType.SATURATION, value=1.0, backend="b", path="/p", window_ts=0
        )
        mp_low = MetricPoint(
            signal=SignalType.SATURATION, value=0.0, backend="b", path="/p", window_ts=0
        )
        assert mp_high.value == 1.0
        assert mp_low.value == 0.0

    def test_metric_point_is_immutable(self) -> None:
        mp = MetricPoint(signal=SignalType.TRAFFIC, value=1.0, backend="b", path="/p", window_ts=0)
        with pytest.raises(ValidationError):
            mp.value = 2.0  # type: ignore[misc]


class TestAnalyticsResult:
    def test_full_result_all_signals_present(self) -> None:
        result = AnalyticsResult(
            backend="web-servers",
            path="/api/v1/orders",
            window="5m",
            window_start_iso="2026-05-17T14:30:00Z",
            traffic=TrafficMetric(total_requests=1842, rps=6.14),
            errors=ErrorMetric(rate_4xx=0.012, rate_5xx=0.002, total_4xx=22, total_5xx=4),
            latency_ms={"p50": 32.0, "p95": 145.0, "p99": 412.0},
            saturation=SaturationMetric(high_wait_pct=3.2, threshold_wait_ms=50),
        )
        dumped = result.model_dump(exclude_none=True)
        assert dumped["traffic"]["total_requests"] == 1842
        assert dumped["errors"]["total_4xx"] == 22
        assert dumped["latency_ms"]["p99"] == 412.0
        assert dumped["saturation"]["high_wait_pct"] == 3.2

    def test_partial_result_absent_signals_excluded(self) -> None:
        # Spec LIM-02 §3.6: absent fields must not appear as null — they must be omitted
        result = AnalyticsResult(
            backend="web-servers",
            path="/api/v1/orders",
            window="5m",
            window_start_iso="2026-05-17T14:30:00Z",
            traffic=TrafficMetric(total_requests=100, rps=0.33),
        )
        dumped = result.model_dump(exclude_none=True)
        assert "traffic" in dumped
        assert "errors" not in dumped
        assert "latency_ms" not in dumped
        assert "saturation" not in dumped

    def test_aggregated_path_marker(self) -> None:
        # Spec LIM-02 §3.5: path="*" when multi-path aggregation is active
        result = AnalyticsResult(
            backend="web-servers",
            path="*",
            window="5m",
            window_start_iso="2026-05-17T14:30:00Z",
        )
        assert result.path == "*"

    def test_latency_ms_accepts_arbitrary_percentile_keys(self) -> None:
        result = AnalyticsResult(
            backend="b",
            path="/p",
            window="1m",
            window_start_iso="2026-05-17T14:30:00Z",
            latency_ms={"p50": 48.0, "p75": 90.0, "p99": 512.0},
        )
        assert result.latency_ms is not None
        assert result.latency_ms["p75"] == 90.0

    def test_empty_result_no_signals(self) -> None:
        result = AnalyticsResult(
            backend="b", path="/p", window="5m", window_start_iso="2026-05-17T14:30:00Z"
        )
        dumped = result.model_dump(exclude_none=True)
        assert "traffic" not in dumped
        assert "errors" not in dumped
        assert "latency_ms" not in dumped
        assert "saturation" not in dumped


class TestTrafficMetric:
    def test_rps_is_float(self) -> None:
        m = TrafficMetric(total_requests=1842, rps=6.14)
        assert isinstance(m.rps, float)


class TestErrorMetric:
    def test_all_error_fields(self) -> None:
        m = ErrorMetric(rate_4xx=0.012, rate_5xx=0.002, total_4xx=22, total_5xx=4)
        assert m.total_4xx == 22
        assert m.rate_5xx == 0.002


class TestSaturationMetric:
    def test_fields(self) -> None:
        m = SaturationMetric(high_wait_pct=3.2, threshold_wait_ms=50)
        assert m.high_wait_pct == 3.2
        assert m.threshold_wait_ms == 50
