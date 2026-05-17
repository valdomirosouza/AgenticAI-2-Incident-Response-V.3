"""Domain exceptions for the log-ingestion-and-metrics service."""

from __future__ import annotations


class MetricStoreError(Exception):
    """Raised when a metric write to the backing store fails (Spec LIM-01 §3.7)."""


class IngestionError(Exception):
    """Raised when batch ingestion cannot proceed due to a non-validation failure."""
