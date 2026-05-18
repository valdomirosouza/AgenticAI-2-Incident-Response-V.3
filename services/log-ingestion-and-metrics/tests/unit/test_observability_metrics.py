"""Unit tests for log_ingestion.observability.metrics (Spec LIM-01 §3.8, Spec LIM-02 §3.7).

Strategy: reset module state between tests by clearing the private globals so each test
exercises a fresh configure() call. No network I/O — the OTel SDK is configured without
an OTLP exporter so all calls go to the default no-op metric reader.
"""

from __future__ import annotations

import importlib

import pytest

import log_ingestion.observability.metrics as metrics_mod


def _reset_module() -> None:
    """Force the module back to unconfigured state."""
    metrics_mod._configured = False  # noqa: SLF001
    metrics_mod._ingestion_events = None  # noqa: SLF001
    metrics_mod._ingestion_batches = None  # noqa: SLF001
    metrics_mod._analytics_seconds = None  # noqa: SLF001


# ── _size_bucket ───────────────────────────────────────────────────────────────


class TestSizeBucket:
    def test_one_is_small(self) -> None:
        assert metrics_mod._size_bucket(1) == "1-10"  # noqa: SLF001

    def test_ten_is_small(self) -> None:
        assert metrics_mod._size_bucket(10) == "1-10"  # noqa: SLF001

    def test_eleven_is_medium(self) -> None:
        assert metrics_mod._size_bucket(11) == "11-100"  # noqa: SLF001

    def test_hundred_is_medium(self) -> None:
        assert metrics_mod._size_bucket(100) == "11-100"  # noqa: SLF001

    def test_hundred_one_is_large(self) -> None:
        assert metrics_mod._size_bucket(101) == "101-1000"  # noqa: SLF001

    def test_thousand_is_large(self) -> None:
        assert metrics_mod._size_bucket(1000) == "101-1000"  # noqa: SLF001


# ── No-op when not configured ──────────────────────────────────────────────────


class TestNoOpWhenUnconfigured:
    def setup_method(self) -> None:
        _reset_module()

    def test_record_ingestion_event_is_noop(self) -> None:
        # Must not raise even when instruments are None
        metrics_mod.record_ingestion_event("web", "accepted", 5)

    def test_record_ingestion_batch_is_noop(self) -> None:
        metrics_mod.record_ingestion_batch(50)

    def test_record_analytics_query_is_noop(self) -> None:
        metrics_mod.record_analytics_query("all", "5m", "hit", 0.012)


# ── configure() ────────────────────────────────────────────────────────────────


class TestConfigure:
    def setup_method(self) -> None:
        _reset_module()

    def test_configure_sets_configured_flag(self) -> None:
        metrics_mod.configure()
        assert metrics_mod._configured is True  # noqa: SLF001

    def test_configure_creates_instruments(self) -> None:
        metrics_mod.configure()
        assert metrics_mod._ingestion_events is not None  # noqa: SLF001
        assert metrics_mod._ingestion_batches is not None  # noqa: SLF001
        assert metrics_mod._analytics_seconds is not None  # noqa: SLF001

    def test_configure_is_idempotent(self) -> None:
        metrics_mod.configure()
        first_ref = metrics_mod._ingestion_events  # noqa: SLF001
        metrics_mod.configure()  # second call — should be a no-op
        assert metrics_mod._ingestion_events is first_ref  # noqa: SLF001

    def test_configure_without_endpoint_does_not_raise(self) -> None:
        metrics_mod.configure(otlp_endpoint=None)

    def test_configure_with_endpoint_does_not_raise(self) -> None:
        # Providing an endpoint string should not raise even if no collector is running.
        # The SDK will fail lazily on export, not on configure.
        metrics_mod.configure(otlp_endpoint="http://localhost:4317")


# ── record_* after configure ───────────────────────────────────────────────────


class TestRecordAfterConfigure:
    def setup_method(self) -> None:
        _reset_module()
        metrics_mod.configure()

    def test_record_ingestion_event_does_not_raise(self) -> None:
        metrics_mod.record_ingestion_event("api-servers", "accepted", 10)

    def test_record_ingestion_event_parse_error(self) -> None:
        metrics_mod.record_ingestion_event("_unknown", "parse_error", 2)

    def test_record_ingestion_event_store_error(self) -> None:
        metrics_mod.record_ingestion_event("web", "store_error", 1)

    def test_record_ingestion_batch_small(self) -> None:
        metrics_mod.record_ingestion_batch(1)

    def test_record_ingestion_batch_medium(self) -> None:
        metrics_mod.record_ingestion_batch(50)

    def test_record_ingestion_batch_large(self) -> None:
        metrics_mod.record_ingestion_batch(999)

    def test_record_analytics_query_hit(self) -> None:
        metrics_mod.record_analytics_query("all", "5m", "hit", 0.005)

    def test_record_analytics_query_miss(self) -> None:
        metrics_mod.record_analytics_query("latency", "1m", "miss", 0.001)

    def test_record_analytics_query_all_windows(self) -> None:
        for w in ("1m", "5m", "15m", "1h"):
            metrics_mod.record_analytics_query("traffic", w, "hit", 0.002)

    def test_record_analytics_query_all_signals(self) -> None:
        for sig in ("all", "traffic", "error", "latency", "saturation"):
            metrics_mod.record_analytics_query(sig, "5m", "hit", 0.003)
