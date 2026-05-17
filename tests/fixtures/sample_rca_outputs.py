"""RCA hypothesis fixtures matching spec 10 — derived from corpus P01–P12 (RULE-C02).

These fixtures represent expected LLM outputs validated against the RCAHypothesis schema.
Confidence scores reflect values reported or implied in the source papers.
"""

from __future__ import annotations

# P01 — latency RCA hypothesis (Chen et al., FSE 2019 pattern)
RCA_P01_LATENCY = {
    "incident_id": "INC-P01-001",
    "root_cause": "Payment gateway upstream connection pool exhausted — concurrent requests exceeded pool limit of 50",
    "contributing_factors": [
        "Black Friday traffic spike: 4.2x normal RPS on payment-service",
        "Connection pool max_size=50 not scaled proportionally to traffic forecast",
        "Circuit breaker threshold too sensitive — tripped at 73% failure rate instead of 90%",
    ],
    "evidence": [
        "prometheus: payment_service_upstream_connection_pool_active{upstream=payment-gateway} == 50 (saturated)",
        'loki: circuit_breaker_open event at 09:42:00 with failure_rate=0.73',
        "tempo: p99 span latency increased from 120ms to 2340ms over 3-minute window",
    ],
    "confidence": 0.89,
    "explanation": (
        "Connection pool saturation is the proximate cause: when pool hits max_size=50, "
        "new requests queue and timeout after 5s, producing the observed p99=2340ms. "
        "The traffic spike (4.2x RPS) is the triggering condition. "
        "Circuit breaker mis-configuration amplified user impact by failing fast too early."
    ),
}

# P03 — cascade error rate RCA (Wang et al., TSC 2021 pattern)
RCA_P03_CASCADE = {
    "incident_id": "INC-P03-001",
    "root_cause": "Primary database connection refused — all authentication queries failed, cascading to downstream services",
    "contributing_factors": [
        "DB primary ran out of max_connections (100) during scheduled maintenance window",
        "Lack of connection pooling on user-auth service side",
        "No graceful degradation path for auth failures in cart-service or checkout-service",
    ],
    "evidence": [
        'loki: db_connection_refused events at 03:06:44–03:06:50 with host=db-primary',
        "loki: health_check_failed with consecutive=10 at 03:07:00",
        "tempo: error propagation chain: user-auth → cart-service → checkout-service spans all show status=503",
    ],
    "confidence": 0.93,
    "explanation": (
        "Root cause is database connection exhaustion on db-primary triggered during maintenance. "
        "user-auth has no pgbouncer — direct connections hit max_connections=100 limit. "
        "The cascade is structural: cart-service and checkout-service have no circuit breaker "
        "on the auth dependency, so they propagate 503s directly to clients."
    ),
}

# P04 — OOMKilled availability RCA (She et al., ICSE-SEIP 2021 pattern)
RCA_P04_OOM = {
    "incident_id": "INC-P04-001",
    "root_cause": "Container OOMKilled — inventory-service memory limit (512Mi) exceeded by nightly batch import job running in-process",
    "contributing_factors": [
        "Batch import job allocated 1.4GB for full-catalogue CSV processing",
        "Memory limit of 512Mi was set for steady-state API traffic, not batch load",
        "No memory-based HPA policy — pod was not pre-scaled before batch window",
    ],
    "evidence": [
        "loki: memory_pressure warnings at 490Mi and 509Mi/512Mi limit before kill",
        'loki: kubelet OOMKilled event at 22:51:03',
        "kubernetes events: container restart count went from 0 to 1 in production namespace",
    ],
    "confidence": 0.97,
    "explanation": (
        "The OOMKill is deterministic: batch job allocates ~1.4GB but container limit is 512Mi. "
        "No pre-scaling or memory reservation was configured for the nightly batch window. "
        "Fix: separate batch job into a dedicated Job resource with its own memory budget, "
        "or increase limit to 2Gi with HPA min=2 during batch window."
    ),
}

# P12 — multi-hop low-confidence RCA (Soldani & Brogi 2022 pattern — below threshold)
RCA_P12_LOW_CONFIDENCE = {
    "incident_id": "INC-P12-001",
    "root_cause": "db-replica replication lag exceeded 30s — read queries routed to lagging replica returned stale data",
    "contributing_factors": [
        "Network throughput bottleneck on replication link during peak write period",
        "product-service read replica selection policy: round-robin without lag awareness",
    ],
    "evidence": [
        "loki: replication_lag_high events at 18s and 31s at 16:21:30 and 16:21:45",
        "loki: stale_read_detected at 16:22:00 with lag_seconds=31",
        "tempo: product-service upstream p99 latency spike to 4100ms at 16:22:10",
    ],
    "confidence": 0.54,  # Below MIN_CONFIDENCE=0.6 — triggers LOW CONFIDENCE label
    "explanation": (
        "Replication lag is the most likely cause based on log correlation, but "
        "the network bottleneck root cause cannot be fully confirmed without network "
        "metrics which are unavailable in current observability data. "
        "Human review of network telemetry is required before action."
    ),
}

ALL_RCA_FIXTURES = [RCA_P01_LATENCY, RCA_P03_CASCADE, RCA_P04_OOM, RCA_P12_LOW_CONFIDENCE]
