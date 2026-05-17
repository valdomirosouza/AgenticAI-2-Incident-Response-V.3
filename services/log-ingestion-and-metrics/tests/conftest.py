"""Shared pytest fixtures for the log-ingestion-and-metrics test suite.

Fixture data is derived from the confirmed HAProxy JSON schema in Spec LIM-01 §3.1.
"""

from __future__ import annotations

from typing import Any

import pytest

from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry

# Canonical sample entry matching the schema in Spec LIM-01 §3.1.
_HAPROXY_ENTRY_DICT: dict[str, Any] = {
    "timestamp": "2024-06-20T15:56:09",
    "client_ip": "192.168.1.50",
    "client_port": 44321,
    "frontend": "http-in",
    "backend": "web-servers",
    "server": "web-01",
    "status_code": 200,
    "bytes_read": 1450,
    "request": "GET /api/v1/data HTTP/1.1",
    "termination_state": "--",
    "timers": {
        "total_time": 105,
        "wait": 2,
        "connect": 1,
        "response": 102,
    },
}


@pytest.fixture
def haproxy_entry_dict() -> dict[str, Any]:
    return dict(_HAPROXY_ENTRY_DICT)


@pytest.fixture
def haproxy_entry() -> HaproxyLogEntry:
    return HaproxyLogEntry.model_validate(_HAPROXY_ENTRY_DICT)


@pytest.fixture
def error_5xx_entry_dict(haproxy_entry_dict: dict[str, Any]) -> dict[str, Any]:
    haproxy_entry_dict["status_code"] = 503
    return haproxy_entry_dict


@pytest.fixture
def abnormal_termination_entry_dict(haproxy_entry_dict: dict[str, Any]) -> dict[str, Any]:
    haproxy_entry_dict["termination_state"] = "SD"
    return haproxy_entry_dict


@pytest.fixture
def high_wait_entry_dict(haproxy_entry_dict: dict[str, Any]) -> dict[str, Any]:
    haproxy_entry_dict["timers"]["wait"] = 80
    return haproxy_entry_dict


@pytest.fixture
def error_4xx_entry_dict(haproxy_entry_dict: dict[str, Any]) -> dict[str, Any]:
    haproxy_entry_dict["status_code"] = 404
    return haproxy_entry_dict


@pytest.fixture
def query_string_entry_dict(haproxy_entry_dict: dict[str, Any]) -> dict[str, Any]:
    haproxy_entry_dict["request"] = "POST /api/v1/users?dry_run=1 HTTP/1.1"
    return haproxy_entry_dict
