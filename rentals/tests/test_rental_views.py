"""Tests for rental API endpoints."""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from cars.models import Car
from customers.models import Customer
from rentals.models import Rental


@pytest.mark.django_db
class TestRentalCreateView:
    def test_create_rental(
        self, auth_client: APIClient, economic_car: Car, customer: Customer
    ) -> None:
        data = {
            "car_id": str(economic_car.id),
            "customer_name": "John Doe",
            "customer_email": customer.email,
            "days": 3,
        }
        response = auth_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 201
        assert response.data["data"]["customer_name"] == "John Doe"
        assert Decimal(response.data["data"]["total_cost"]) == Decimal("150.00")

        economic_car.refresh_from_db()
        assert not economic_car.available

    def test_create_rental_with_short_discount(
        self, auth_client: APIClient, economic_car: Car, customer: Customer
    ) -> None:
        data = {
            "car_id": str(economic_car.id),
            "customer_name": "John Doe",
            "customer_email": customer.email,
            "days": 4,
        }
        response = auth_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 201
        expected = Decimal("50.00") * 4 * Decimal("0.95")
        assert Decimal(response.data["data"]["total_cost"]) == expected

    def test_create_rental_with_week_discount(
        self, auth_client: APIClient, economic_car: Car, customer: Customer
    ) -> None:
        data = {
            "car_id": str(economic_car.id),
            "customer_name": "John Doe",
            "customer_email": customer.email,
            "days": 8,
        }
        response = auth_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 201
        expected = Decimal("50.00") * 8 * Decimal("0.90")
        assert Decimal(response.data["data"]["total_cost"]) == expected

    def test_create_rental_nonexistent_car(
        self, auth_client: APIClient, customer: Customer
    ) -> None:
        data = {
            "car_id": str(uuid.uuid4()),
            "customer_name": "John",
            "customer_email": customer.email,
            "days": 3,
        }
        response = auth_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_create_rental_unavailable_car(
        self, auth_client: APIClient, unavailable_car: Car, customer: Customer
    ) -> None:
        data = {
            "car_id": str(unavailable_car.id),
            "customer_name": "John",
            "customer_email": customer.email,
            "days": 3,
        }
        response = auth_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "car_not_available"

    def test_create_rental_invalid_data(self, auth_client: APIClient) -> None:
        response = auth_client.post("/api/rentals/create/", {}, format="json")
        assert response.status_code == 400

    def test_create_rental_invalid_email(self, auth_client: APIClient, economic_car: Car) -> None:
        data = {
            "car_id": str(economic_car.id),
            "customer_name": "John",
            "customer_email": "not-an-email",
            "days": 3,
        }
        response = auth_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 400

    def test_create_rental_zero_days(
        self, auth_client: APIClient, economic_car: Car, customer: Customer
    ) -> None:
        data = {
            "car_id": str(economic_car.id),
            "customer_name": "John",
            "customer_email": customer.email,
            "days": 0,
        }
        response = auth_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 400

    def test_requires_authentication(self, api_client: APIClient, economic_car: Car) -> None:
        data = {"car_id": str(economic_car.id), "days": 3}
        response = api_client.post("/api/rentals/create/", data, format="json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestRentalReturnView:
    def test_return_on_time(self, auth_client: APIClient, active_rental: Rental) -> None:
        response = auth_client.post(f"/api/rentals/{active_rental.id}/return/")
        assert response.status_code == 200
        rental_data = response.data["data"]
        assert rental_data["returned"] is True
        assert rental_data["late_fee"] is None

    def test_return_late(
        self,
        auth_client: APIClient,
        economic_car: Car,
        customer: Customer,
    ) -> None:
        now = timezone.now()
        rental = Rental.objects.create(
            car=economic_car,
            customer=customer,
            customer_name="John Doe",
            customer_email=customer.email,
            start_date=now - timedelta(days=5),
            end_date=now - timedelta(days=2),
            total_cost=Decimal("250.00"),
        )
        response = auth_client.post(f"/api/rentals/{rental.id}/return/")
        assert response.status_code == 200
        rental_data = response.data["data"]
        assert rental_data["returned"] is True
        assert rental_data["late_fee"] is not None
        assert Decimal(rental_data["late_fee"]) > 0

    def test_return_already_returned(self, auth_client: APIClient, returned_rental: Rental) -> None:
        response = auth_client.post(f"/api/rentals/{returned_rental.id}/return/")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "rental_already_returned"

    def test_return_nonexistent_rental(self, auth_client: APIClient) -> None:
        response = auth_client.post(f"/api/rentals/{uuid.uuid4()}/return/")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_requires_authentication(self, api_client: APIClient, active_rental: Rental) -> None:
        response = api_client.post(f"/api/rentals/{active_rental.id}/return/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestRentalListView:
    def test_list_rentals(self, auth_client: APIClient, active_rental: Rental) -> None:
        response = auth_client.get("/api/rentals/")
        assert response.status_code == 200
        # CustomerScopedQuerysetMixin: customer sees only their own rentals
        assert response.data["meta"]["count"] == 1
        assert len(response.data["data"]) == 1

    def test_list_empty(self, auth_client: APIClient) -> None:
        response = auth_client.get("/api/rentals/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 0
        assert len(response.data["data"]) == 0

    def test_staff_sees_all_rentals(
        self,
        staff_client: APIClient,
        active_rental: Rental,
        staff_user: Customer,
        economic_car: Car,
    ) -> None:
        # Create a rental belonging to staff user
        now = timezone.now()
        Rental.objects.create(
            car=economic_car,
            customer=staff_user,
            customer_name="Admin",
            customer_email=staff_user.email,
            start_date=now,
            end_date=now + timedelta(days=1),
            total_cost=Decimal("50.00"),
        )
        response = staff_client.get("/api/rentals/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 2

    def test_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.get("/api/rentals/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestRentalDetailView:
    def test_customer_can_get_own_rental(
        self, auth_client: APIClient, active_rental: Rental
    ) -> None:
        response = auth_client.get(f"/api/rentals/{active_rental.id}/")
        assert response.status_code == 200
        assert response.data["data"]["id"] == str(active_rental.id)

    def test_staff_can_get_any_rental(
        self, staff_client: APIClient, active_rental: Rental
    ) -> None:
        response = staff_client.get(f"/api/rentals/{active_rental.id}/")
        assert response.status_code == 200
        assert response.data["data"]["id"] == str(active_rental.id)

    def test_customer_getting_other_customer_rental_returns_not_found(
        self, auth_client: APIClient, economic_car: Car, staff_user: Customer
    ) -> None:
        now = timezone.now()
        rental = Rental.objects.create(
            car=economic_car,
            customer=staff_user,
            customer_name="Admin",
            customer_email=staff_user.email,
            start_date=now,
            end_date=now + timedelta(days=1),
            total_cost=Decimal("50.00"),
        )
        response = auth_client.get(f"/api/rentals/{rental.id}/")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_get_nonexistent_rental_returns_not_found(self, auth_client: APIClient) -> None:
        response = auth_client.get(f"/api/rentals/{uuid.uuid4()}/")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_requires_authentication(self, api_client: APIClient, active_rental: Rental) -> None:
        response = api_client.get(f"/api/rentals/{active_rental.id}/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestCustomerRentalListView:
    def test_list_own_rentals(
        self, auth_client: APIClient, active_rental: Rental, customer: Customer
    ) -> None:
        response = auth_client.get(f"/api/rentals/customer/{customer.email}/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 1

    def test_list_customer_no_rentals(self, auth_client: APIClient, customer: Customer) -> None:
        response = auth_client.get(f"/api/rentals/customer/{customer.email}/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 0

    def test_staff_can_list_any_customer(
        self,
        staff_client: APIClient,
        active_rental: Rental,
        customer: Customer,
    ) -> None:
        response = staff_client.get(f"/api/rentals/customer/{customer.email}/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 1

    def test_customer_cannot_access_other_customer(
        self,
        auth_client: APIClient,
        staff_user: Customer,
    ) -> None:
        response = auth_client.get(f"/api/rentals/customer/{staff_user.email}/")
        assert response.status_code in (403, 400)


@pytest.mark.django_db
class TestRentalStatsView:
    def test_stats_with_data(self, staff_client: APIClient, active_rental: Rental) -> None:
        response = staff_client.get("/api/rentals/stats/")
        assert response.status_code == 200
        stats = response.data["data"]
        assert stats["total_rentals"] == 1
        assert stats["active_rentals"] == 1

    def test_stats_empty(self, staff_client: APIClient) -> None:
        response = staff_client.get("/api/rentals/stats/")
        assert response.status_code == 200
        assert response.data["data"]["total_rentals"] == 0

    def test_requires_admin(self, auth_client: APIClient) -> None:
        response = auth_client.get("/api/rentals/stats/")
        assert response.status_code == 403
