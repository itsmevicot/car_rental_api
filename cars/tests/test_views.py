"""Tests for car API endpoints."""

import uuid

import pytest
from rest_framework.test import APIClient

from cars.models import Car


@pytest.mark.django_db
class TestCarListView:
    def test_list_available_cars(self, api_client: APIClient, economic_car: Car) -> None:
        response = api_client.get("/api/cars/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 1
        assert response.data["meta"]["next"] is None
        assert response.data["meta"]["previous"] is None
        assert len(response.data["data"]) == 1
        assert response.data["data"][0]["brand"] == economic_car.brand

    def test_excludes_unavailable_cars(
        self, api_client: APIClient, economic_car: Car, unavailable_car: Car
    ) -> None:
        response = api_client.get("/api/cars/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 1
        assert len(response.data["data"]) == 1
        car_ids = [c["id"] for c in response.data["data"]]
        assert str(economic_car.id) in car_ids
        assert str(unavailable_car.id) not in car_ids

    def test_empty_when_no_available_cars(
        self, api_client: APIClient, unavailable_car: Car
    ) -> None:
        response = api_client.get("/api/cars/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 0
        assert len(response.data["data"]) == 0

    def test_includes_category_field(self, api_client: APIClient, premium_car: Car) -> None:
        response = api_client.get("/api/cars/")
        assert response.status_code == 200
        assert response.data["data"][0]["category"] == "premium"

    def test_no_auth_required(self, api_client: APIClient) -> None:
        """Car list is publicly accessible."""
        response = api_client.get("/api/cars/")
        assert response.status_code == 200

    def test_supports_page_size_query_param(
        self, api_client: APIClient, economic_car: Car, standard_car: Car, premium_car: Car
    ) -> None:
        response = api_client.get("/api/cars/?page_size=2")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 3
        assert len(response.data["data"]) == 2
        assert response.data["meta"]["next"] is not None

    def test_staff_can_include_unavailable_cars(
        self, staff_client: APIClient, economic_car: Car, unavailable_car: Car
    ) -> None:
        response = staff_client.get("/api/cars/?include_unavailable=true")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 2
        car_ids = [c["id"] for c in response.data["data"]]
        assert str(economic_car.id) in car_ids
        assert str(unavailable_car.id) in car_ids

    def test_public_cannot_include_unavailable_cars(
        self, api_client: APIClient, economic_car: Car, unavailable_car: Car
    ) -> None:
        response = api_client.get("/api/cars/?include_unavailable=true")
        assert response.status_code == 403
        assert response.data["error"]["code"] == "permission_denied"

    def test_regular_customer_cannot_include_unavailable_cars(
        self, authenticated_client: APIClient, economic_car: Car, unavailable_car: Car
    ) -> None:
        response = authenticated_client.get("/api/cars/?include_unavailable=true")
        assert response.status_code == 403
        assert response.data["error"]["code"] == "permission_denied"


@pytest.mark.django_db
class TestCarDetailView:
    def test_get_existing_car(self, api_client: APIClient, economic_car: Car) -> None:
        response = api_client.get(f"/api/cars/{economic_car.id}/")
        assert response.status_code == 200
        assert response.data["data"]["brand"] == "Toyota"
        assert response.data["data"]["model"] == "Corolla"

    def test_get_nonexistent_car(self, api_client: APIClient) -> None:
        fake_id = uuid.uuid4()
        response = api_client.get(f"/api/cars/{fake_id}/")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_category_economic(self, api_client: APIClient, economic_car: Car) -> None:
        response = api_client.get(f"/api/cars/{economic_car.id}/")
        assert response.data["data"]["category"] == "economic"

    def test_category_standard(self, api_client: APIClient, standard_car: Car) -> None:
        response = api_client.get(f"/api/cars/{standard_car.id}/")
        assert response.data["data"]["category"] == "standard"

    def test_public_cannot_get_unavailable_car(
        self, api_client: APIClient, unavailable_car: Car
    ) -> None:
        response = api_client.get(f"/api/cars/{unavailable_car.id}/")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_regular_customer_cannot_get_unavailable_car(
        self, authenticated_client: APIClient, unavailable_car: Car
    ) -> None:
        response = authenticated_client.get(f"/api/cars/{unavailable_car.id}/")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_staff_can_get_unavailable_car(
        self, staff_client: APIClient, unavailable_car: Car
    ) -> None:
        response = staff_client.get(f"/api/cars/{unavailable_car.id}/")
        assert response.status_code == 200
        assert response.data["data"]["id"] == str(unavailable_car.id)
        assert response.data["data"]["available"] is False
