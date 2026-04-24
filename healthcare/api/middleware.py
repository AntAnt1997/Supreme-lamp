"""FastAPI middleware – CORS, rate limiting, request logging."""

import logging
import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %d %.1fms",
            request.method, request.url.path, response.status_code, duration,
        )
        return response


# Simple in-memory rate limiter (suitable for single-instance deployments)
_request_counts: dict = defaultdict(list)
_RATE_LIMIT = 120       # requests
_RATE_WINDOW = 60       # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - _RATE_WINDOW

        # Prune old entries
        _request_counts[client_ip] = [
            t for t in _request_counts[client_ip] if t > window_start
        ]

        if len(_request_counts[client_ip]) >= _RATE_LIMIT:
            return Response(
                content='{"detail": "Rate limit exceeded. Please slow down."}',
                status_code=429,
                media_type="application/json",
            )

        _request_counts[client_ip].append(now)
        return await call_next(request)
