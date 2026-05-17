"""Unit tests for HaproxyLogEntry, HaproxyTimers, HaproxyLogBatch.

Covers Spec LIM-01 §3.1 (schema validation) and §3.7 (batch size contract).
All fixtures use the canonical schema from conftest.py; no synthetic data (RULE-C02).
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from log_ingestion.domain.models.haproxy_log import (
    HaproxyLogBatch,
    HaproxyLogEntry,
    HaproxyTimers,
)


class TestHaproxyTimers:
    def test_valid_timers_accepted(self) -> None:
        t = HaproxyTimers(total_time=105, wait=2, connect=1, response=102)
        assert t.total_time == 105
        assert t.wait == 2

    def test_zero_timers_accepted(self) -> None:
        t = HaproxyTimers(total_time=0, wait=0, connect=0, response=0)
        assert t.total_time == 0

    def test_negative_total_time_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HaproxyTimers(total_time=-1, wait=0, connect=0, response=0)

    def test_negative_wait_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HaproxyTimers(total_time=0, wait=-5, connect=0, response=0)

    def test_timers_are_immutable(self) -> None:
        t = HaproxyTimers(total_time=10, wait=1, connect=1, response=8)
        with pytest.raises(ValidationError):
            t.total_time = 99  # type: ignore[misc]


class TestHaproxyLogEntry:
    def test_valid_entry_parsed(self, haproxy_entry: HaproxyLogEntry) -> None:
        assert haproxy_entry.backend == "web-servers"
        assert haproxy_entry.server == "web-01"
        assert haproxy_entry.status_code == 200
        assert haproxy_entry.timers.total_time == 105

    def test_clean_termination_state(self, haproxy_entry: HaproxyLogEntry) -> None:
        assert haproxy_entry.termination_state == "--"

    def test_path_and_query_in_request_field(self, haproxy_entry: HaproxyLogEntry) -> None:
        assert haproxy_entry.request == "GET /api/v1/data HTTP/1.1"

    def test_client_ip_present_at_validation_boundary(self, haproxy_entry: HaproxyLogEntry) -> None:
        # PII is accepted for schema validation; callers must not persist it (ADR-0028)
        assert haproxy_entry.client_ip == "192.168.1.50"

    def test_status_code_above_599_rejected(self, haproxy_entry_dict: dict[str, Any]) -> None:
        haproxy_entry_dict["status_code"] = 700
        with pytest.raises(ValidationError):
            HaproxyLogEntry.model_validate(haproxy_entry_dict)

    def test_negative_status_code_rejected(self, haproxy_entry_dict: dict[str, Any]) -> None:
        haproxy_entry_dict["status_code"] = -1
        with pytest.raises(ValidationError):
            HaproxyLogEntry.model_validate(haproxy_entry_dict)

    def test_invalid_client_port_rejected(self, haproxy_entry_dict: dict[str, Any]) -> None:
        haproxy_entry_dict["client_port"] = 99999
        with pytest.raises(ValidationError):
            HaproxyLogEntry.model_validate(haproxy_entry_dict)

    def test_negative_bytes_read_rejected(self, haproxy_entry_dict: dict[str, Any]) -> None:
        haproxy_entry_dict["bytes_read"] = -1
        with pytest.raises(ValidationError):
            HaproxyLogEntry.model_validate(haproxy_entry_dict)

    def test_entry_is_immutable(self, haproxy_entry: HaproxyLogEntry) -> None:
        with pytest.raises(ValidationError):
            haproxy_entry.backend = "other"  # type: ignore[misc]

    def test_5xx_status_accepted_as_valid_entry(self, error_5xx_entry_dict: dict[str, Any]) -> None:
        entry = HaproxyLogEntry.model_validate(error_5xx_entry_dict)
        assert entry.status_code == 503

    def test_abnormal_termination_state_accepted(
        self, abnormal_termination_entry_dict: dict[str, Any]
    ) -> None:
        entry = HaproxyLogEntry.model_validate(abnormal_termination_entry_dict)
        assert entry.termination_state == "SD"


class TestHaproxyLogBatch:
    def test_single_entry_batch(self, haproxy_entry_dict: dict[str, Any]) -> None:
        batch = HaproxyLogBatch.model_validate([haproxy_entry_dict])
        assert len(batch.root) == 1

    def test_batch_within_limit(self, haproxy_entry_dict: dict[str, Any]) -> None:
        batch = HaproxyLogBatch.model_validate([haproxy_entry_dict] * 10)
        assert len(batch.root) == 10

    def test_batch_at_exact_limit(self, haproxy_entry_dict: dict[str, Any]) -> None:
        batch = HaproxyLogBatch.model_validate([haproxy_entry_dict] * 1000)
        assert len(batch.root) == 1000

    def test_batch_exceeds_limit_rejected(self, haproxy_entry_dict: dict[str, Any]) -> None:
        # Spec LIM-01 §3.7: 1001 entries → 422 before any processing
        with pytest.raises(ValidationError):
            HaproxyLogBatch.model_validate([haproxy_entry_dict] * 1001)
