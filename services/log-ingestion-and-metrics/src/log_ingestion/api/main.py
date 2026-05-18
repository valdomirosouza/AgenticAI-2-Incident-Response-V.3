"""FastAPI application entrypoint for the log-ingestion-and-metrics service.

Wires adapters to ports during lifespan startup and tears them down on shutdown.
All configuration is read from environment variables (Spec LIM-01 §3.8, ADR-0033).

Environment variables:
  REDIS_URL             — Redis connection URL (default: redis://localhost:6379/0)
  LIM_SAT_THRESHOLD_MS  — Saturation wait threshold in ms (default: 50)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import FastAPI

from log_ingestion.adapters.ingestion_service import IngestionService
from log_ingestion.adapters.redis_metric_adapter import RedisMetricAdapter
from log_ingestion.api.routers import health, ingestion
from log_ingestion.domain.services.log_parser import LogParser


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    sat_threshold_ms = int(os.getenv("LIM_SAT_THRESHOLD_MS", "50"))

    redis_client: aioredis.Redis = aioredis.from_url(redis_url, decode_responses=False)
    metric_store = RedisMetricAdapter(redis_client)
    parser = LogParser(sat_threshold_ms=sat_threshold_ms)

    app.state.metric_store = metric_store
    app.state.ingestion_service = IngestionService(store=metric_store, parser=parser)

    yield

    await redis_client.aclose()


app = FastAPI(
    title="log-ingestion-and-metrics",
    description="HAProxy log ingestion and Golden Signal analytics — Incident Response Copilot",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingestion.router)
app.include_router(health.router)
