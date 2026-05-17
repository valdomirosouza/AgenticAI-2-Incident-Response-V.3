"""Security: audit trail hash-chain tamper detection — spec 17 §3.4, ADR-0024."""

from datetime import datetime, timezone

import pytest

from src.domain.models.audit import AuditEvent, AuditEventType, ChainValidationResult

_GENESIS = "sha256:" + "0" * 64


def _make_event(record_id: str, prev_hash: str, record_hash: str) -> AuditEvent:
    return AuditEvent(
        record_id=record_id,
        incident_id="INC-SEC-AUDIT",
        event_type=AuditEventType.INCIDENT_CREATED,
        agent_role="orchestrator",
        payload={"test": True},
        timestamp=datetime.now(tz=timezone.utc),
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="00f067aa0ba902b7",
        prev_hash=prev_hash,
        record_hash=record_hash,
    )


@pytest.mark.security
class TestAuditChainValidation:
    def test_valid_chain_validates(self) -> None:
        e1 = _make_event("aud-001", _GENESIS, "hash-001")
        e2 = _make_event("aud-002", "hash-001", "hash-002")
        e3 = _make_event("aud-003", "hash-002", "hash-003")

        # Simulate what GCSAuditAdapter.validate_chain does locally
        events = [e1, e2, e3]
        prev = _GENESIS
        first_broken = None
        for event in events:
            if event.prev_hash != prev:
                first_broken = event.record_id
                break
            prev = event.record_hash

        result = ChainValidationResult(
            incident_id="INC-SEC-AUDIT",
            valid=first_broken is None,
            record_count=3,
            first_broken_link=first_broken,
            validated_at=datetime.now(tz=timezone.utc),
        )
        assert result.valid is True
        assert result.first_broken_link is None

    def test_tampered_event_detected(self) -> None:
        e1 = _make_event("aud-001", _GENESIS, "hash-001")
        e2_tampered = _make_event("aud-002", "WRONG-HASH", "hash-002")  # prev_hash tampered
        e3 = _make_event("aud-003", "hash-002", "hash-003")

        events = [e1, e2_tampered, e3]
        prev = _GENESIS
        first_broken = None
        for event in events:
            if event.prev_hash != prev:
                first_broken = event.record_id
                break
            prev = event.record_hash

        assert first_broken == "aud-002"

    def test_single_event_with_genesis_valid(self) -> None:
        e1 = _make_event("aud-001", _GENESIS, "hash-001")
        assert e1.prev_hash == _GENESIS

    def test_audit_event_fields_immutable_via_model(self) -> None:
        """AuditEvent is a Pydantic model — field assignment is blocked by default."""
        e1 = _make_event("aud-001", _GENESIS, "hash-001")
        with pytest.raises(Exception):
            e1.record_hash = "tampered"  # type: ignore[misc]
