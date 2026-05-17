"""W3C TraceContext middleware — propagates traceparent into request state (spec 07)."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Extracts or generates W3C traceparent; injects trace_id + span_id into request.state."""

    async def dispatch(self, request: Request, call_next) -> Response:
        traceparent = request.headers.get("traceparent", "")
        trace_id, span_id = _parse_or_generate(traceparent)
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        response = await call_next(request)
        response.headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
        return response


def _parse_or_generate(traceparent: str) -> tuple[str, str]:
    parts = traceparent.split("-")
    if len(parts) == 4 and parts[0] == "00":
        return parts[1], parts[2]
    trace_id = uuid.uuid4().hex + uuid.uuid4().hex  # 32 hex chars
    span_id = uuid.uuid4().hex[:16]
    return trace_id, span_id
