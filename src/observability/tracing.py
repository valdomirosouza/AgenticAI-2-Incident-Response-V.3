"""OpenTelemetry tracing bootstrap — spec 07, ADR-0002."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def configure_tracing(service_name: str = "incident-response-copilot") -> None:
    """Bootstrap OTel SDK with OTLP exporter pointing at Tempo."""
    try:
        from opentelemetry import trace  # type: ignore[import]
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore[import]
        from opentelemetry.sdk.resources import Resource  # type: ignore[import]
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import]
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore[import]

        from src.observability.pii_span_processor import PiiSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(PiiSpanProcessor())
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo:4317")
                )
            )
        )
        trace.set_tracer_provider(provider)
        logger.info("otel_tracing_configured", extra={"service_name": service_name})
    except ImportError:
        logger.warning("opentelemetry_sdk_not_installed_tracing_disabled")
