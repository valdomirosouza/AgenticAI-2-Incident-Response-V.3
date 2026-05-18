# syntax=docker/dockerfile:1
# Multi-stage build for log-ingestion-and-metrics service.
# Spec LIM-01 §3.8 / Spec LIM-02 §3.8 — container runtime requirements.

# ── Builder ────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir --target /install .

# ── Runtime ────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user — principle of least privilege
RUN useradd --no-create-home --shell /usr/sbin/nologin lim

ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /install /usr/local/lib/python3.12/site-packages/
COPY --from=builder /build/src /app/src

WORKDIR /app

USER lim

EXPOSE 8000

# Environment variables (all have safe defaults; override at runtime):
#   REDIS_URL             — Redis connection URL          (default: redis://localhost:6379/0)
#   LIM_SAT_THRESHOLD_MS  — Saturation threshold in ms   (default: 50)
#   OTLP_ENDPOINT         — OTel collector gRPC endpoint (default: unset → no-op exporter)

CMD ["uvicorn", "log_ingestion.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"
