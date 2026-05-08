"""Operational endpoint smoke tests."""

from unittest.mock import patch

import pytest
from django.db.utils import OperationalError
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_check_returns_healthy(self) -> None:
        api_client = APIClient()
        response = api_client.get("/api/health/")
        assert response.status_code == 200
        assert response.data["data"]["status"] == "healthy"

    def test_health_check_returns_unhealthy_when_database_fails(self) -> None:
        api_client = APIClient()
        with patch("core.views.connection.ensure_connection", side_effect=OperationalError):
            response = api_client.get("/api/health/")
        assert response.status_code == 503
        assert response.data["data"]["status"] == "unhealthy"

    def test_readiness_returns_database_status(self) -> None:
        api_client = APIClient()
        response = api_client.get("/api/ready/")
        assert response.status_code == 200
        assert response.data["data"] == {"status": "healthy", "database": "up"}

    def test_readiness_returns_unhealthy_when_database_fails(self) -> None:
        api_client = APIClient()
        with patch("core.views.connection.ensure_connection", side_effect=OperationalError):
            response = api_client.get("/api/ready/")
        assert response.status_code == 503
        assert response.data["data"] == {"status": "unhealthy", "database": "down"}

    def test_schema_endpoint_is_available(self) -> None:
        api_client = APIClient()
        response = api_client.get("/api/schema/")
        assert response.status_code == 200

    def test_swagger_ui_is_available(self) -> None:
        api_client = APIClient()
        response = api_client.get("/api/docs/")
        assert response.status_code == 200
        assert "swaggerSettings" in response.content.decode()

    def test_redoc_is_available(self) -> None:
        api_client = APIClient()
        response = api_client.get("/api/redoc/")
        assert response.status_code == 200
        assert "redoc.standalone.js" in response.content.decode()
