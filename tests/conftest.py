"""Shared pytest fixtures for all test layers."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.domain.models.agent_message import AgentRole, MessageType
from src.domain.models.audit import AuditEventType
from src.domain.models.incident import Incident, IncidentStatus, Severity
from src.domain.models.remediation import ActionType, ApprovalToken, RemediationProposal
from src.domain.models.rca import RCAHypothesis
from tests.fixtures.corpus_incidents import INCIDENT_P01_LATENCY, INCIDENT_P04_AVAILABILITY
from tests.fixtures.sample_rca_outputs import RCA_P01_LATENCY, RCA_P04_OOM


# ── Shared constants ───────────────────────────────────────────────────────────

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
SPAN_ID = "00f067aa0ba902b7"
INCIDENT_ID = "INC-TEST-001"


# ── Incident fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def incident_p01() -> Incident:
    """P1 latency incident from corpus P01 (Chen et al., FSE 2019)."""
    return Incident(
        incident_id=INCIDENT_P01_LATENCY["incident_id"],
        title=INCIDENT_P01_LATENCY["title"],
        severity=Severity.P2,
        affected_service=INCIDENT_P01_LATENCY["affected_service"],
        status=IncidentStatus.DETECTING,
        detected_at=datetime.fromisoformat(INCIDENT_P01_LATENCY["detected_at"].replace("Z", "+00:00")),
        source=INCIDENT_P01_LATENCY["source"],
    )


@pytest.fixture
def incident_p04() -> Incident:
    """P1 availability incident from corpus P04 (She et al., ICSE-SEIP 2021)."""
    return Incident(
        incident_id=INCIDENT_P04_AVAILABILITY["incident_id"],
        title=INCIDENT_P04_AVAILABILITY["title"],
        severity=Severity.P1,
        affected_service=INCIDENT_P04_AVAILABILITY["affected_service"],
        status=IncidentStatus.INVESTIGATING,
        detected_at=datetime.fromisoformat(
            INCIDENT_P04_AVAILABILITY["detected_at"].replace("Z", "+00:00")
        ),
        source=INCIDENT_P04_AVAILABILITY["source"],
    )


# ── RCA fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def rca_p01() -> RCAHypothesis:
    """High-confidence RCA from corpus P01 (confidence=0.89)."""
    return RCAHypothesis(**RCA_P01_LATENCY)


@pytest.fixture
def rca_p04() -> RCAHypothesis:
    """High-confidence RCA from corpus P04 (confidence=0.97)."""
    return RCAHypothesis(**RCA_P04_OOM)


# ── RemediationProposal fixtures ───────────────────────────────────────────────

@pytest.fixture
def proposal_pod_restart() -> RemediationProposal:
    return RemediationProposal(
        incident_id=INCIDENT_ID,
        action_type=ActionType.PRODUCTION_POD_RESTART,
        target_service="inventory-service",
        parameters={"namespace": "production", "deployment": "inventory-service"},
        rationale="OOMKilled pod — restart with memory limit increased to 2Gi",
        predicted_effect="Service availability restored within 30s",
        confidence=0.97,
        risk_estimate="low",
    )


@pytest.fixture
def proposal_scale_up() -> RemediationProposal:
    return RemediationProposal(
        incident_id=INCIDENT_ID,
        action_type=ActionType.PRODUCTION_SCALE_UP,
        target_service="payment-service",
        parameters={"replicas": 10},
        rationale="Connection pool exhausted — scale horizontally to distribute load",
        predicted_effect="p99 latency returns below 500ms threshold within 60s",
        confidence=0.89,
        risk_estimate="low",
    )


@pytest.fixture
def proposal_data_delete() -> RemediationProposal:
    """BLOCKED action — data delete (spec 16 §3.5)."""
    return RemediationProposal(
        incident_id=INCIDENT_ID,
        action_type=ActionType.PRODUCTION_DATA_DELETE,
        target_service="order-service",
        parameters={"table": "dead_orders"},
        rationale="Clear stale records",
        predicted_effect="Reduced storage pressure",
        confidence=0.80,
        risk_estimate="high",
    )


# ── ApprovalToken fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def valid_approval_token() -> ApprovalToken:
    now = datetime.now(tz=timezone.utc)
    return ApprovalToken(
        token_id=uuid4(),
        incident_id=INCIDENT_ID,
        action_type=ActionType.PRODUCTION_POD_RESTART,
        approver_role="sre-lead",
        approved_at=now,
        expires_at=now + timedelta(minutes=15),
        signature="valid-hmac-placeholder",
    )


@pytest.fixture
def expired_approval_token() -> ApprovalToken:
    past = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    return ApprovalToken(
        token_id=uuid4(),
        incident_id=INCIDENT_ID,
        action_type=ActionType.PRODUCTION_POD_RESTART,
        approver_role="sre-lead",
        approved_at=past - timedelta(minutes=15),
        expires_at=past,
        signature="expired-hmac-placeholder",
    )


# ── Port mocks ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_audit_port():
    port = AsyncMock()
    port.append = AsyncMock(return_value=None)
    port.validate_chain = AsyncMock()
    port.get_events = AsyncMock(return_value=[])
    return port


@pytest.fixture
def mock_llm_port():
    port = AsyncMock()
    return port


@pytest.fixture
def mock_hitl_port():
    port = AsyncMock()
    port.validate_token = AsyncMock(return_value=None)
    return port


@pytest.fixture
def mock_observability_port():
    port = AsyncMock()
    port.query_logs = AsyncMock(return_value=[])
    port.query_metrics = AsyncMock(return_value=[])
    port.query_traces = AsyncMock(return_value=[])
    return port
