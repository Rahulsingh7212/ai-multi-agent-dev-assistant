from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable
import logging
import time
import traceback

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware.

    Catches all unhandled exceptions and returns
    consistent error responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            logger.error(f"❌ Unhandled exception: {exc}")
            logger.error(traceback.format_exc())

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": str(exc),
                    "path": str(request.url),
                    "method": request.method,
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all incoming requests with timing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request
        logger.info(
            f"📥 {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)

            # Log response with timing
            duration = time.time() - start_time
            logger.info(
                f"📤 {request.method} {request.url.path} "
                f"→ {response.status_code} ({duration:.3f}s)"
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(round(duration, 3))

            return response

        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                f"❌ {request.method} {request.url.path} "
                f"→ ERROR after {duration:.3f}s: {exc}"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    For production, use Redis-backed rate limiting.
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_counts: dict = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries
        self._request_counts = {
            k: v for k, v in self._request_counts.items()
            if current_time - v["first_request"] < self.window_seconds
        }

        # Check rate
        if client_ip in self._request_counts:
            entry = self._request_counts[client_ip]
            if entry["count"] >= self.max_requests:
                logger.warning(f"⚠️  Rate limit exceeded for {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Max {self.max_requests} requests per {self.window_seconds}s",
                    },
                )
            entry["count"] += 1
        else:
            self._request_counts[client_ip] = {
                "count": 1,
                "first_request": current_time,
            }

        return await call_next(request)