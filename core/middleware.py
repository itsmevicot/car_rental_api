"""Shared middleware."""

import time
from collections.abc import Callable

import structlog
from django.http import HttpRequest, HttpResponse

logger = structlog.get_logger("core.middleware")


class RequestLoggingMiddleware:
    """Log every HTTP request with method, path, status, and duration."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Store the next middleware callable.

        Args:
            get_response: Callable that executes the rest of the middleware stack.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and emit a structured access log.

        Args:
            request: Incoming Django HTTP request.

        Returns:
            HttpResponse: Response produced by the downstream application.
        """
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        logger.info(
            "http_request",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )

        return response
