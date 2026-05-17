"""Domain service: HAProxy log entry → Golden Signal MetricPoints.

Supports RQ1 (MTTD reduction): transforms validated log entries into the four Golden
Signal MetricPoints that the metric store adapter persists to Redis (Spec LIM-01 §3.2–§3.5).

No I/O — pure transformation. Callers decide which window sizes to apply (ADR-0002).
"""

from __future__ import annotations

from datetime import datetime

from log_ingestion.domain.models.haproxy_log import HaproxyLogEntry
from log_ingestion.domain.models.metric import MetricPoint, SignalType

_DEFAULT_SAT_THRESHOLD_MS: int = 50
_SUPPORTED_WINDOWS: frozenset[int] = frozenset({60, 300, 900, 3600})


class LogParser:
    """Converts a single HaproxyLogEntry into four MetricPoints for one time window.

    Instantiate once per service lifetime. Thread-safe (no mutable state).
    """

    def __init__(self, sat_threshold_ms: int = _DEFAULT_SAT_THRESHOLD_MS) -> None:
        self._sat_threshold_ms = sat_threshold_ms

    def parse(self, entry: HaproxyLogEntry, window_seconds: int) -> list[MetricPoint]:
        """Return four MetricPoints (TRAFFIC, ERROR, LATENCY, SATURATION) for one window.

        Args:
            entry: Validated HAProxy log entry. `client_ip` is never read here (ADR-0028).
            window_seconds: Bucket size in seconds. Must be one of 60, 300, 900, 3600.

        Raises:
            ValueError: if window_seconds is not a supported value.
        """
        if window_seconds not in _SUPPORTED_WINDOWS:
            raise ValueError(
                f"window_seconds must be one of {sorted(_SUPPORTED_WINDOWS)}, got {window_seconds}"
            )

        path = self._extract_path(entry.request)
        window_ts = self._window_ts(entry.timestamp, window_seconds)

        return [
            MetricPoint(
                signal=SignalType.TRAFFIC,
                value=1.0,
                backend=entry.backend,
                path=path,
                window_ts=window_ts,
            ),
            MetricPoint(
                signal=SignalType.ERROR,
                value=self._error_value(entry),
                backend=entry.backend,
                path=path,
                window_ts=window_ts,
            ),
            MetricPoint(
                signal=SignalType.LATENCY,
                value=float(entry.timers.total_time),
                backend=entry.backend,
                path=path,
                window_ts=window_ts,
            ),
            MetricPoint(
                signal=SignalType.SATURATION,
                value=self._saturation_value(entry),
                backend=entry.backend,
                path=path,
                window_ts=window_ts,
            ),
        ]

    # ── private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _extract_path(request_line: str) -> str:
        """Strip method, protocol version, and query string from the request line.

        Spec LIM-01 §3.2: 'METHOD /path[?query] HTTP/x.x' → '/path'
        """
        _, raw_path, _ = request_line.split(" ", 2)
        return raw_path.split("?")[0]

    @staticmethod
    def _window_ts(timestamp: datetime, window_seconds: int) -> int:
        """Floor-align a timestamp to its window bucket (Spec LIM-01 §3.5)."""
        return int(timestamp.timestamp()) // window_seconds * window_seconds

    def _error_value(self, entry: HaproxyLogEntry) -> float:
        """Return 1.0 if the entry represents an error, 0.0 otherwise.

        Error conditions (Spec LIM-01 §3.4):
          - status_code in 400–599
          - termination_state != '--' (abnormal connection termination)
        """
        if entry.termination_state != "--":
            return 1.0
        if entry.status_code >= 400:
            return 1.0
        return 0.0

    def _saturation_value(self, entry: HaproxyLogEntry) -> float:
        """Return 1.0 if backend queue wait exceeded the saturation threshold (Spec LIM-01 §3.4)."""
        return 1.0 if entry.timers.wait > self._sat_threshold_ms else 0.0
