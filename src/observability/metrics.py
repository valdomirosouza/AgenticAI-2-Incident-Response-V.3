"""OpenTelemetry metrics bootstrap — Golden Signals + MTTD/MTTR (spec 06, ADR-0002)."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def configure_metrics(service_name: str = "incident-response-copilot") -> None:
    """Bootstrap OTel metrics SDK with Prometheus exporter."""
    try:
        from opentelemetry import metrics  # type: ignore[import]
        from opentelemetry.exporter.prometheus import PrometheusMetricReader  # type: ignore[import]
        from opentelemetry.sdk.metrics import MeterProvider  # type: ignore[import]
        from opentelemetry.sdk.resources import Resource  # type: ignore[import]

        resource = Resource.create({"service.name": service_name})
        reader = PrometheusMetricReader()
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)

        meter = metrics.get_meter(service_name)

        # MTTD / MTTR SLO histograms (spec 06 §3.1)
        meter.create_histogram("incident_mttd_seconds", description="Mean Time to Detect — seconds")
        meter.create_histogram("incident_mttr_seconds", description="Mean Time to Recover — seconds")

        # Agent confidence distribution (ADR-0021 LLM09)
        meter.create_histogram(
            "agent_confidence",
            description="LLM output confidence score per agent role",
        )

        logger.info("otel_metrics_configured", extra={"service_name": service_name})
    except ImportError:
        logger.warning("opentelemetry_sdk_not_installed_metrics_disabled")
