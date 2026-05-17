"""FastAPI application entry point — spec 01, ADR-0002."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import incidents, health
from src.api.middleware.trace_context import TraceContextMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Incident Response Copilot",
    version="0.5.0",
    description="Agentic AI Copilot for Incident Response — MTTD/MTTR reduction.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(TraceContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # Populated from environment at deploy time — RULE-C03
    allow_methods=["GET", "POST"],
    allow_headers=["traceparent", "tracestate", "X-Request-ID"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
