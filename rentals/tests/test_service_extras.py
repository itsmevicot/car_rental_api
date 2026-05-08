"""Extra rental service and view coverage."""

from unittest.mock import patch

import pytest
from rest_framework.test import APIRequestFactory

from core.exceptions import AuthorizationError, NotFoundError
from customers.models import Customer
from rentals.services import RentalService
from rentals.views import CustomerRentalListByIdView


@pytest.mark.django_db
class TestRentalServiceExtras:
    def test_display_name_prefers_supplied_name(self, customer: Customer) -> None:
        assert RentalService.display_name(customer, "Supplied") == "Supplied"

    def test_display_name_falls_back_to_full_name(self, customer: Customer) -> None:
        assert RentalService.display_name(customer) == "John Doe"

    def test_resolve_customer_returns_existing(self, customer: Customer) -> None:
        service = RentalService()
        assert service.resolve_customer(customer.email, "Ignored", is_staff=False) == customer

    def test_resolve_customer_creates_for_staff(self) -> None:
        service = RentalService()
        customer = service.resolve_customer(
            "staff-created@example.com", "Staff Created", is_staff=True
        )
        assert customer is not None
        assert customer.email == "staff-created@example.com"

    def test_resolve_customer_returns_none_for_non_staff(self) -> None:
        service = RentalService()
        assert service.resolve_customer("missing@example.com", "Missing", is_staff=False) is None

    def test_return_rental_forbidden_for_other_customer(self, active_rental) -> None:
        service = RentalService()
        other_customer = Customer.objects.create_user(
            email="other-customer@example.com",
            password="secret123",
            first_name="Other",
            last_name="Customer",
        )
        with pytest.raises(AuthorizationError):
            service.return_rental(active_rental.id, actor=other_customer)

    def test_list_helpers(self, active_rental) -> None:
        service = RentalService()
        assert list(service.list_by_customer(active_rental.customer)) == [active_rental]
        assert list(service.empty_list()) == []

    def test_list_by_customer_id_not_found(self) -> None:
        service = RentalService()
        with pytest.raises(NotFoundError):
            service.list_by_customer_id("0192d5e0-7a1a-7b3a-8c4d-1234567890ab")


@pytest.mark.django_db
class TestRentalViewExtras:
    def test_staff_create_rental_creates_missing_customer(self, staff_client, economic_car) -> None:
        response = staff_client.post(
            "/api/rentals/create/",
            {
                "car_id": str(economic_car.id),
                "customer_name": "Created By Staff",
                "customer_email": "new-customer@example.com",
                "days": 3,
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["data"]["customer_email"] == "new-customer@example.com"

    def test_staff_create_runtime_error_when_resolution_returns_none(
        self, staff_client, economic_car
    ) -> None:
        with (
            patch("rentals.views._rental_service.resolve_customer", return_value=None),
            pytest.raises(RuntimeError),
        ):
            staff_client.post(
                "/api/rentals/create/",
                {
                    "car_id": str(economic_car.id),
                    "customer_name": "No Customer",
                    "customer_email": "none@example.com",
                    "days": 3,
                },
                format="json",
            )

    def test_customer_rental_list_by_id(self, staff_client, active_rental) -> None:
        response = staff_client.get(f"/api/rentals/customers/{active_rental.customer_id}/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 1

    def test_customer_rental_list_by_id_get_queryset_fallback(self, active_rental) -> None:
        factory = APIRequestFactory()
        view = CustomerRentalListByIdView()
        view.request = factory.get("/api/rentals/")
        view.kwargs = {"customer_id": str(active_rental.customer_id)}
        queryset = view.get_queryset()
        assert list(queryset) == [active_rental]
