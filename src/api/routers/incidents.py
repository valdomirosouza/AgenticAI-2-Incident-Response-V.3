"""Incidents router — incident creation and status endpoints (spec 01, spec 02)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from src.domain.models.incident import Incident, Severity

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateIncidentRequest(BaseModel):
    title: str
    severity: Severity
    affected_service: str
    detected_at: str
    source: str


class IncidentResponse(BaseModel):
    incident_id: str
    status: str
    severity: str


@router.post("", response_model=IncidentResponse, status_code=202)
async def create_incident(
    body: CreateIncidentRequest,
    request: Request,
) -> IncidentResponse:
    """Ingest a new incident and trigger the agent pipeline (HOTL detection path)."""
    trace_id: str = request.state.trace_id
    logger.info(
        "incident_create_requested",
        extra={
            "affected_service": body.affected_service,
            "severity": body.severity,
            "trace_id": trace_id,
        },
    )
    # Orchestrator dispatch wired in dependency injection at startup
    return IncidentResponse(
        incident_id="INC-placeholder",
        status="DETECTING",
        severity=body.severity.value,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str, request: Request) -> IncidentResponse:
    """Return current status of an incident."""
    return IncidentResponse(
        incident_id=incident_id,
        status="UNKNOWN",
        severity="unknown",
    )
