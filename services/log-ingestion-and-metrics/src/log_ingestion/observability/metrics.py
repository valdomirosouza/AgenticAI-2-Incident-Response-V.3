"""OTel metric instruments for the log-ingestion-and-metrics service.

Instruments (Spec LIM-01 §3.8, Spec LIM-02 §3.7):
  lim_ingestion_events_total   — Counter  labels: backend, result
  lim_ingestion_batches_total  — Counter  labels: size_bucket
  lim_analytics_query_seconds  — Histogram labels: signal, window, result

Call ``configure(otlp_endpoint)`` once at lifespan startup. All record_*
helpers are no-ops until the module is configured, so tests that do not call
configure() produce no side-effects.
"""

from __future__ import annotations

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

_configured: bool = False

# Instrument references — None until configure() is called
_ingestion_events: metrics.Counter | None = None
_ingestion_batches: metrics.Counter | None = None
_analytics_seconds: metrics.Histogram | None = None


def configure(otlp_endpoint: str | None = None) -> None:
    """Initialise the OTel MeterProvider and create the service instruments.

    Idempotent: subsequent calls after the first are ignored.
    When *otlp_endpoint* is None the MeterProvider uses the default no-op exporter
    (useful for local development without a collector).
    """
    global _configured, _ingestion_events, _ingestion_batches, _analytics_seconds  # noqa: PLW0603

    if _configured:
        return

    resource = Resource.create({"service.name": "log-ingestion-and-metrics"})

    if otlp_endpoint:
        exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=15_000)
        provider: MeterProvider = MeterProvider(resource=resource, metric_readers=[reader])
    else:
        provider = MeterProvider(resource=resource)

    metrics.set_meter_provider(provider)
    meter = metrics.get_meter("log_ingestion", version="0.1.0")

    _ingestion_events = meter.create_counter(
        name="lim_ingestion_events_total",
        description="Total ingestion entry outcomes by backend and result",
        unit="1",
    )
    _ingestion_batches = meter.create_counter(
        name="lim_ingestion_batches_total",
        description="Total ingestion batch calls by size bucket",
        unit="1",
    )
    _analytics_seconds = meter.create_histogram(
        name="lim_analytics_query_seconds",
        description="Duration of GET /analytics calls by signal, window, and result",
        unit="s",
    )
    _configured = True


def _size_bucket(batch_size: int) -> str:
    if batch_size <= 10:
        return "1-10"
    if batch_size <= 100:
        return "11-100"
    return "101-1000"


def record_ingestion_event(backend: str, result: str, count: int = 1) -> None:
    """Increment ``lim_ingestion_events_total`` for *count* entries with the given *result*."""
    if _ingestion_events is None:
        return
    _ingestion_events.add(count, {"backend": backend, "result": result})


def record_ingestion_batch(batch_size: int) -> None:
    """Increment ``lim_ingestion_batches_total`` for a single batch call."""
    if _ingestion_batches is None:
        return
    _ingestion_batches.add(1, {"size_bucket": _size_bucket(batch_size)})


def record_analytics_query(
    signal: str,
    window: str,
    result: str,
    duration_s: float,
) -> None:
    """Record a single ``lim_analytics_query_seconds`` observation."""
    if _analytics_seconds is None:
        return
    _analytics_seconds.record(duration_s, {"signal": signal, "window": window, "result": result})
