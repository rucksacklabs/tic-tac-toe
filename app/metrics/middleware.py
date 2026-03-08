"""
Purpose: HTTP metrics middleware for FastAPI.
Architecture: Infrastructure Layer (Metrics).
Notes: Records request count and duration for every HTTP request.
       Retrieves MetricsClient from app.state.metrics (set at startup in main.py).
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        metrics = request.app.state.metrics
        tags = {
            "endpoint": request.url.path,
            "method": request.method,
        }
        metrics.increment(
            "http.request.count",
            tags={**tags, "status_code": str(response.status_code)},
        )
        metrics.timing("http.request.duration_ms", duration_ms, tags=tags)

        return response
