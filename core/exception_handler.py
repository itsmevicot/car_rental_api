"""Centralized DRF exception handling."""

from typing import Any

import structlog
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.exceptions import ServiceError

logger = structlog.get_logger(__name__)


def custom_exception_handler(exc: Exception, context: Any) -> Response | None:
    """Build a standardized HTTP error response.

    Args:
        exc: The exception raised while handling the request.
        context: DRF exception handler context.

    Returns:
        A normalized DRF response when the exception is recognized, otherwise
        ``None`` to delegate to Django/DRF defaults.
    """
    if isinstance(exc, ServiceError):
        logger.warning(
            "service_error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
        )
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=exc.status_code,
        )

    if isinstance(exc, ValidationError):

        def _serialize(detail):
            if isinstance(detail, list):
                return [str(item) for item in detail]
            if isinstance(detail, dict):
                return {k: _serialize(v) for k, v in detail.items()}
            return str(detail)

        serialized = _serialize(exc.detail)
        logger.warning("validation_error", detail=serialized)
        return Response(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Invalid input",
                    "details": exc.detail,
                }
            },
            status=exc.status_code,
        )

    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, APIException):
        detail = exc.detail
        if isinstance(detail, dict):
            message = str(detail.get("detail", exc.default_detail))
        elif isinstance(detail, list):
            message = str(detail[0]) if detail else exc.default_detail
        else:
            message = str(detail)

        logger.warning(
            "api_error",
            code=exc.default_code,
            message=message,
            status_code=response.status_code,
        )
        return Response(
            {"error": {"code": exc.default_code, "message": message}},
            status=response.status_code,
        )

    if response is None:
        logger.exception("unhandled_exception", exc_info=exc)

    return response
