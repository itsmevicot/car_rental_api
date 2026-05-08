"""Tests for auth and profile views."""

import pytest


@pytest.mark.django_db
class TestRegisterView:
    def test_register_customer(self, api_client) -> None:
        response = api_client.post(
            "/api/auth/register/",
            {
                "email": "register@example.com",
                "first_name": "Reg",
                "last_name": "User",
                "password": "secret123",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["data"]["email"] == "register@example.com"

    def test_register_invalid_payload(self, api_client) -> None:
        response = api_client.post("/api/auth/register/", {"email": "bad"}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestMeView:
    def test_me_returns_authenticated_user(self, auth_client) -> None:
        response = auth_client.get("/api/auth/me/")
        assert response.status_code == 200
        assert response.data["data"]["email"] == "john@example.com"

    def test_me_requires_authentication(self, api_client) -> None:
        response = api_client.get("/api/auth/me/")
        assert response.status_code == 401
