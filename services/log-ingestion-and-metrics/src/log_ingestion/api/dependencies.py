"""FastAPI dependency factories for the log-ingestion-and-metrics service.

Both dependencies read objects placed on ``app.state`` during the lifespan startup
(``api/main.py``). Tests override these via ``app.dependency_overrides`` to inject
stubs without touching the lifespan.
"""

from __future__ import annotations

from fastapi import Request

from log_ingestion.ports.ingestion_port import IngestionPort
from log_ingestion.ports.metric_store_port import MetricStorePort


def get_metric_store(request: Request) -> MetricStorePort:
    return request.app.state.metric_store  # type: ignore[no-any-return]


def get_ingestion_service(request: Request) -> IngestionPort:
    return request.app.state.ingestion_service  # type: ignore[no-any-return]
