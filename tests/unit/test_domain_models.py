"""Unit tests for domain models — spec 02, 16, 17 (RULE-C02 corpus fixtures)."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.domain.models.incident import Incident, IncidentStatus, Severity
from src.domain.models.remediation import (
    ActionType,
    ApprovalToken,
    BLOCKED_ACTION_TYPES,
    HITL_ACTION_TYPES,
    RemediationProposal,
)
from src.domain.models.rca import RCAHypothesis
from src.domain.models.audit import AuditEvent, AuditEventType
from tests.fixtures.corpus_incidents import (
    INCIDENT_P01_LATENCY,
    INCIDENT_P04_AVAILABILITY,
    ALL_CORPUS_INCIDENTS,
)
from tests.fixtures.sample_rca_outputs import RCA_P01_LATENCY, RCA_P04_OOM, RCA_P12_LOW_CONFIDENCE


@pytest.mark.unit
class TestIncidentModel:
    def test_incident_mttd_computed(self, incident_p04) -> None:
        """mttd_seconds is computable when resolved_at is set — corpus P04 pattern."""
        resolved = incident_p04.detected_at + timedelta(seconds=INCIDENT_P04_AVAILABILITY["mttd_seconds"])
        updated = incident_p04.model_copy(update={"resolved_at": resolved})
        assert updated.mttd_seconds == INCIDENT_P04_AVAILABILITY["mttd_seconds"]

    def test_incident_mttr_computed(self, incident_p04) -> None:
        resolved = incident_p04.detected_at + timedelta(seconds=INCIDENT_P04_AVAILABILITY["mttr_seconds"])
        updated = incident_p04.model_copy(update={"resolved_at": resolved})
        assert updated.mttr_seconds == INCIDENT_P04_AVAILABILITY["mttr_seconds"]

    def test_incident_mttd_none_when_not_resolved(self, incident_p01) -> None:
        assert incident_p01.mttd_seconds is None

    @pytest.mark.parametrize("raw", ALL_CORPUS_INCIDENTS)
    def test_corpus_incident_can_be_created(self, raw: dict) -> None:
        inc = Incident(
            incident_id=raw["incident_id"],
            title=raw["title"],
            severity=Severity(raw["severity"]),
            affected_service=raw["affected_service"],
            status=IncidentStatus.DETECTING,
            detected_at=datetime.fromisoformat(raw["detected_at"].replace("Z", "+00:00")),
            source=raw["source"],
        )
        assert inc.incident_id == raw["incident_id"]


@pytest.mark.unit
class TestRemediationSets:
    def test_hitl_set_contains_pod_restart(self) -> None:
        assert ActionType.PRODUCTION_POD_RESTART in HITL_ACTION_TYPES

    def test_hitl_set_contains_all_seven_types(self) -> None:
        assert len(HITL_ACTION_TYPES) == 7

    def test_blocked_set_contains_three_types(self) -> None:
        assert len(BLOCKED_ACTION_TYPES) == 3

    def test_blocked_and_hitl_are_disjoint(self) -> None:
        assert BLOCKED_ACTION_TYPES.isdisjoint(HITL_ACTION_TYPES)

    def test_data_delete_is_blocked(self) -> None:
        assert ActionType.PRODUCTION_DATA_DELETE in BLOCKED_ACTION_TYPES

    def test_iam_change_is_blocked(self) -> None:
        assert ActionType.PRODUCTION_IAM_CHANGE in BLOCKED_ACTION_TYPES

    def test_firewall_change_is_blocked(self) -> None:
        assert ActionType.PRODUCTION_FIREWALL_CHANGE in BLOCKED_ACTION_TYPES


@pytest.mark.unit
class TestRCAHypothesis:
    def test_high_confidence_rca_valid(self) -> None:
        rca = RCAHypothesis(**RCA_P04_OOM)
        assert rca.confidence == 0.97
        assert rca.incident_id == "INC-P04-001"

    def test_low_confidence_rca_valid(self) -> None:
        rca = RCAHypothesis(**RCA_P12_LOW_CONFIDENCE)
        assert rca.confidence == 0.54

    def test_confidence_must_be_between_0_and_1(self) -> None:
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            RCAHypothesis(**{**RCA_P01_LATENCY, "confidence": 1.5})


@pytest.mark.unit
class TestApprovalToken:
    def test_valid_token_creates(self, valid_approval_token) -> None:
        assert valid_approval_token.action_type == ActionType.PRODUCTION_POD_RESTART

    def test_expires_at_must_be_after_approved_at(self) -> None:
        now = datetime.now(tz=timezone.utc)
        token = ApprovalToken(
            token_id=uuid4(),
            incident_id="INC-TEST",
            action_type=ActionType.PRODUCTION_POD_RESTART,
            approver_role="sre-lead",
            approved_at=now,
            expires_at=now + timedelta(minutes=15),
            signature="test-sig",
        )
        assert token.expires_at > token.approved_at
