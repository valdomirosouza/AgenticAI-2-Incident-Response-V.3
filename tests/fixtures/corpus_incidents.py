"""Incident fixtures derived from research corpus papers P1–P19 (RULE-C02).

Sources (ABNT):
  P01 — CHEN, J. et al. Towards intelligent incident management. ESEC/FSE, 2019.
  P02 — GHOSH, S. et al. DeCaf: Diagnosing and triaging performance issues in large-scale
        cloud services. ICSE, 2022.
  P03 — WANG, J. et al. Root cause analysis of anomalies in microservice architectures.
        IEEE Transactions on Services Computing, 2021.
  P04 — SHE, D. et al. Fast outage analysis in large-scale production cloud systems.
        ICSE-SEIP, 2021.
  P06 — NEDELKOSKI, S. et al. Self-supervised log parsing. ECML-PKDD, 2020.
  P12 — SOLDANI, J.; BROGI, A. Anomaly detection and failure root cause analysis in
        (micro)service-based cloud applications. ACM CSUR, 2022.
"""

from __future__ import annotations

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# P01 — Azure cloud service latency incident pattern (Chen et al., FSE 2019)
# ---------------------------------------------------------------------------
INCIDENT_P01_LATENCY = {
    "incident_id": "INC-P01-001",
    "title": "Elevated p99 latency on payment-service API gateway",
    "severity": "P2",
    "affected_service": "payment-service",
    "detected_at": "2023-11-14T09:42:00Z",
    "source": "prometheus_alert",
    "golden_signal": "latency",
    "p99_ms_baseline": 120,
    "p99_ms_observed": 2340,
    "threshold_ms": 500,
    "duration_minutes": 18,
    "mttd_seconds": 214,
    "mttr_seconds": 1080,
}

# ---------------------------------------------------------------------------
# P02 — DeCaf performance degradation pattern (Ghosh et al., ICSE 2022)
# ---------------------------------------------------------------------------
INCIDENT_P02_SATURATION = {
    "incident_id": "INC-P02-001",
    "title": "CPU saturation on order-processing workers — queue depth spike",
    "severity": "P2",
    "affected_service": "order-service",
    "detected_at": "2023-08-22T14:15:00Z",
    "source": "prometheus_alert",
    "golden_signal": "saturation",
    "cpu_utilization_baseline": 0.42,
    "cpu_utilization_observed": 0.97,
    "queue_depth_baseline": 120,
    "queue_depth_observed": 8400,
    "duration_minutes": 34,
    "mttd_seconds": 180,
    "mttr_seconds": 2040,
}

# ---------------------------------------------------------------------------
# P03 — Microservice cascade failure (Wang et al., TSC 2021)
# ---------------------------------------------------------------------------
INCIDENT_P03_ERROR_RATE = {
    "incident_id": "INC-P03-001",
    "title": "HTTP 503 cascade from user-auth to downstream services",
    "severity": "P1",
    "affected_service": "user-auth",
    "detected_at": "2023-06-05T03:07:00Z",
    "source": "prometheus_alert",
    "golden_signal": "errors",
    "error_rate_baseline": 0.002,
    "error_rate_observed": 0.847,
    "affected_downstream": ["cart-service", "checkout-service", "notification-service"],
    "duration_minutes": 52,
    "mttd_seconds": 420,
    "mttr_seconds": 3120,
}

# ---------------------------------------------------------------------------
# P04 — Fast outage pattern: availability drop (She et al., ICSE-SEIP 2021)
# ---------------------------------------------------------------------------
INCIDENT_P04_AVAILABILITY = {
    "incident_id": "INC-P04-001",
    "title": "Full availability drop on inventory-service — pod OOMKilled",
    "severity": "P1",
    "affected_service": "inventory-service",
    "detected_at": "2023-09-30T22:51:00Z",
    "source": "kubernetes_event",
    "golden_signal": "availability",
    "availability_baseline": 0.9998,
    "availability_observed": 0.0,
    "root_cause": "OOMKilled — container memory limit 512Mi exceeded by 3x during batch job",
    "duration_minutes": 11,
    "mttd_seconds": 92,
    "mttr_seconds": 660,
}

# ---------------------------------------------------------------------------
# P06 — Log-anomaly-driven detection (Nedelkoski et al., ECML 2020)
# ---------------------------------------------------------------------------
INCIDENT_P06_LOG_ANOMALY = {
    "incident_id": "INC-P06-001",
    "title": "Abnormal log template spike in recommendation-engine",
    "severity": "P3",
    "affected_service": "recommendation-engine",
    "detected_at": "2023-12-01T11:30:00Z",
    "source": "loki_anomaly_detector",
    "golden_signal": "errors",
    "anomaly_score": 0.91,
    "log_template": "TEMPLATE_ERR_DB_CONN_TIMEOUT",
    "log_volume_baseline_per_min": 12,
    "log_volume_observed_per_min": 3840,
    "duration_minutes": 27,
    "mttd_seconds": 330,
    "mttr_seconds": 1620,
}

# ---------------------------------------------------------------------------
# P12 — Microservice anomaly with multi-hop root cause (Soldani & Brogi 2022)
# ---------------------------------------------------------------------------
INCIDENT_P12_MULTI_HOP = {
    "incident_id": "INC-P12-001",
    "title": "Multi-hop latency degradation: api-gateway → product-service → db-replica",
    "severity": "P2",
    "affected_service": "api-gateway",
    "detected_at": "2024-01-15T16:22:00Z",
    "source": "tempo_trace_anomaly",
    "golden_signal": "latency",
    "root_cause_chain": ["db-replica", "product-service", "api-gateway"],
    "root_cause": "db-replica replication lag exceeded 30s — read queries routed to lagging node",
    "confidence": 0.87,
    "duration_minutes": 41,
    "mttd_seconds": 510,
    "mttr_seconds": 2460,
}

# All corpus incidents as an ordered list for parametrized tests
ALL_CORPUS_INCIDENTS = [
    INCIDENT_P01_LATENCY,
    INCIDENT_P02_SATURATION,
    INCIDENT_P03_ERROR_RATE,
    INCIDENT_P04_AVAILABILITY,
    INCIDENT_P06_LOG_ANOMALY,
    INCIDENT_P12_MULTI_HOP,
]
