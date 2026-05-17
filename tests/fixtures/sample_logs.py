"""Anonymized log samples derived from real incident patterns in corpus P01–P12 (RULE-C02).

All PII has been removed or replaced with placeholders before inclusion.
No customer data, IP addresses, or personal identifiers are present.
"""

from __future__ import annotations

# P01 — latency incident log pattern (payment-service)
LOGS_P01_LATENCY: list[str] = [
    '{"ts":"2023-11-14T09:41:44Z","level":"WARN","service":"payment-service","msg":"upstream_latency_high","upstream":"payment-gateway","p99_ms":1820,"threshold_ms":500}',
    '{"ts":"2023-11-14T09:41:47Z","level":"ERROR","service":"payment-service","msg":"request_timeout","method":"POST","path":"/v1/charge","duration_ms":5001,"status":504}',
    '{"ts":"2023-11-14T09:42:00Z","level":"ERROR","service":"payment-service","msg":"circuit_breaker_open","upstream":"payment-gateway","failure_rate":0.73}',
    '{"ts":"2023-11-14T09:42:14Z","level":"INFO","service":"api-gateway","msg":"upstream_unhealthy","target":"payment-service","consecutive_failures":5}',
]

# P02 — saturation incident log pattern (order-service)
LOGS_P02_SATURATION: list[str] = [
    '{"ts":"2023-08-22T14:14:22Z","level":"WARN","service":"order-service","msg":"queue_depth_high","queue":"order-processing","depth":4200,"threshold":1000}',
    '{"ts":"2023-08-22T14:14:55Z","level":"WARN","service":"order-service","msg":"worker_cpu_high","cpu_pct":94.2,"pid":1001}',
    '{"ts":"2023-08-22T14:15:01Z","level":"ERROR","service":"order-service","msg":"worker_oom_risk","heap_mb":1820,"limit_mb":2048}',
    '{"ts":"2023-08-22T14:15:10Z","level":"ERROR","service":"order-service","msg":"processing_lag","lag_seconds":312,"consumer_group":"order-workers"}',
]

# P03 — error rate cascade (user-auth)
LOGS_P03_ERROR_RATE: list[str] = [
    '{"ts":"2023-06-05T03:06:44Z","level":"ERROR","service":"user-auth","msg":"db_connection_refused","host":"db-primary","port":5432,"attempt":1}',
    '{"ts":"2023-06-05T03:06:45Z","level":"ERROR","service":"user-auth","msg":"db_connection_refused","host":"db-primary","port":5432,"attempt":2}',
    '{"ts":"2023-06-05T03:06:50Z","level":"ERROR","service":"cart-service","msg":"auth_service_unavailable","status":503,"retry":1}',
    '{"ts":"2023-06-05T03:07:00Z","level":"CRITICAL","service":"user-auth","msg":"health_check_failed","consecutive":10}',
    '{"ts":"2023-06-05T03:07:00Z","level":"ERROR","service":"checkout-service","msg":"dependency_unhealthy","dep":"user-auth","error_rate":0.85}',
]

# P04 — availability / OOMKilled (inventory-service)
LOGS_P04_AVAILABILITY: list[str] = [
    '{"ts":"2023-09-30T22:50:42Z","level":"WARN","service":"inventory-service","msg":"memory_pressure","rss_mb":490,"limit_mb":512}',
    '{"ts":"2023-09-30T22:50:55Z","level":"WARN","service":"inventory-service","msg":"memory_pressure","rss_mb":509,"limit_mb":512}',
    # Kubernetes OOMKilled event (anonymized — no node hostname)
    '{"ts":"2023-09-30T22:51:03Z","level":"CRITICAL","source":"kubelet","msg":"container_oom_killed","container":"inventory-service","namespace":"production","reason":"OOMKilled"}',
    '{"ts":"2023-09-30T22:51:05Z","level":"ERROR","service":"api-gateway","msg":"backend_unavailable","backend":"inventory-service","status":503}',
]

# P12 — multi-hop latency (db-replica replication lag)
LOGS_P12_MULTI_HOP: list[str] = [
    '{"ts":"2024-01-15T16:21:30Z","level":"WARN","service":"db-replica","msg":"replication_lag_high","lag_seconds":18,"threshold_seconds":5}',
    '{"ts":"2024-01-15T16:21:45Z","level":"WARN","service":"db-replica","msg":"replication_lag_high","lag_seconds":31,"threshold_seconds":5}',
    '{"ts":"2024-01-15T16:22:00Z","level":"ERROR","service":"product-service","msg":"stale_read_detected","lag_seconds":31,"query":"SELECT inventory WHERE sku=?"}',
    '{"ts":"2024-01-15T16:22:10Z","level":"WARN","service":"api-gateway","msg":"upstream_latency_high","upstream":"product-service","p99_ms":4100}',
]

# Logs containing PII — used to validate pii_sanitizer in security tests
LOGS_WITH_PII: list[str] = [
    # BR CPF embedded in log line (must be redacted)
    '{"ts":"2024-03-01T10:00:00Z","level":"ERROR","service":"billing","msg":"payment_failed","cpf":"123.456.789-09","status":422}',
    # Email address in stack trace
    '{"ts":"2024-03-01T10:00:01Z","level":"ERROR","service":"notification","msg":"smtp_error","recipient":"user@example.com","code":550}',
    # IPv4 in connection refused
    '{"ts":"2024-03-01T10:00:02Z","level":"ERROR","service":"db-client","msg":"connection_refused","host":"10.0.1.42","port":5432}',
]
