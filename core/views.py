"""Core operational views."""

from django.db import connection
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


@extend_schema(tags=["Health"])
class HealthCheckView(APIView):
    """Check service health.

    Confirms that the API process is running and that the database connection
    is available.

    This endpoint is public and intended for monitoring.
    """

    permission_classes = (AllowAny,)

    @extend_schema(responses={200: {"type": "object"}, 503: {"type": "object"}})
    def get(self, request: Request) -> Response:
        """Return healthy when the DB connection is reachable, 503 otherwise."""
        try:
            connection.ensure_connection()
        except OperationalError:
            return Response(
                {"data": {"status": "unhealthy", "database": "down"}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"data": {"status": "healthy"}})


@extend_schema(tags=["Health"])
class ReadinessView(APIView):
    """Check service readiness.

    Confirms whether the API is ready to serve requests and reports the current
    database status.

    This endpoint is public and intended for monitoring.
    """

    permission_classes = (AllowAny,)

    @extend_schema(responses={200: {"type": "object"}, 503: {"type": "object"}})
    def get(self, request: Request) -> Response:
        """Return readiness status and database availability."""
        try:
            connection.ensure_connection()
        except OperationalError:
            return Response(
                {"data": {"status": "unhealthy", "database": "down"}},
                status=503,
            )
        return Response({"data": {"status": "healthy", "database": "up"}})
