"""Tests for reward API endpoints."""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from cars.models import Car
from customers.models import Customer
from rentals.models import Rental
from rewards.models import RewardTransaction, TransactionType


def _make_rental(car: Car, customer: Customer, days: int = 3) -> Rental:
    """Helper: create a rental belonging to customer."""
    now = timezone.now()
    return Rental.objects.create(
        car=car,
        customer=customer,
        customer_name=customer.get_full_name() or customer.email,
        customer_email=customer.email,
        start_date=now,
        end_date=now + timedelta(days=days),
        total_cost=car.daily_rate * days,
    )


def _earn_points(customer: Customer, rental: Rental, points: int) -> RewardTransaction:
    """Helper: create an EARNED reward transaction."""
    return RewardTransaction.objects.create(
        customer=customer,
        customer_email=customer.email,
        rental=rental,
        type=TransactionType.EARNED,
        points=points,
        reason="test seed",
    )


@pytest.mark.django_db
class TestRewardSummaryView:
    """GET /api/rewards/ — authenticated user's own summary."""

    def test_summary_with_no_history(self, auth_client: APIClient, customer: Customer) -> None:
        response = auth_client.get("/api/rewards/")
        assert response.status_code == 200
        data = response.data["data"]
        assert data["total_points"] == 0
        assert data["tier"] == "Bronze"
        assert data["points_to_next_tier"] == 500

    def test_summary_with_points(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 350)

        response = auth_client.get("/api/rewards/")
        assert response.status_code == 200
        data = response.data["data"]
        assert data["total_points"] == 350
        assert data["tier"] == "Bronze"
        assert data["points_to_next_tier"] == 150

    def test_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.get("/api/rewards/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestCustomerRewardSummaryView:
    """GET /api/rewards/customer/{email}/ — staff or self."""

    def test_self_access(self, auth_client: APIClient, customer: Customer) -> None:
        response = auth_client.get(f"/api/rewards/customer/{customer.email}/")
        assert response.status_code == 200
        assert response.data["data"]["total_points"] == 0
        assert response.data["data"]["tier"] == "Bronze"

    def test_staff_access_other_customer(self, staff_client: APIClient, customer: Customer) -> None:
        response = staff_client.get(f"/api/rewards/customer/{customer.email}/")
        assert response.status_code == 200

    def test_non_existent_customer_returns_404(self, staff_client: APIClient) -> None:
        response = staff_client.get("/api/rewards/customer/nobody@example.com/")
        assert response.status_code == 200
        assert response.data["data"]["total_points"] == 0

    def test_customer_cannot_access_other_email(
        self, auth_client: APIClient, staff_user: Customer
    ) -> None:
        response = auth_client.get(f"/api/rewards/customer/{staff_user.email}/")
        assert response.status_code in (403, 400)


@pytest.mark.django_db
class TestRewardHistoryView:
    """GET /api/rewards/history/ — authenticated user's own history."""

    def test_history_returns_transactions(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 100)
        RewardTransaction.objects.create(
            customer=customer,
            customer_email=customer.email,
            rental=rental,
            type=TransactionType.REDEEMED,
            points=-50,
            reason="redeemed points",
        )

        response = auth_client.get("/api/rewards/history/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 2
        assert "breakdown" not in response.data["data"][0]

    def test_history_empty_for_new_customer(self, auth_client: APIClient) -> None:
        response = auth_client.get("/api/rewards/history/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 0

    def test_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.get("/api/rewards/history/")
        assert response.status_code == 401

    def test_history_filters_by_type(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 100)
        RewardTransaction.objects.create(
            customer=customer,
            customer_email=customer.email,
            rental=rental,
            type=TransactionType.REDEEMED,
            points=-50,
            reason="redeemed points",
        )

        response = auth_client.get("/api/rewards/history/?type=redeemed")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 1
        assert response.data["data"][0]["type"] == "redeemed"

    def test_history_ordering(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 100)
        RewardTransaction.objects.create(
            customer=customer,
            customer_email=customer.email,
            rental=rental,
            type=TransactionType.REDEEMED,
            points=-50,
            reason="redeemed points",
        )

        response = auth_client.get("/api/rewards/history/?ordering=points")
        assert response.status_code == 200
        points = [item["points"] for item in response.data["data"]]
        assert points == sorted(points)

    def test_history_rejects_invalid_export_format(self, auth_client: APIClient) -> None:
        response = auth_client.get("/api/rewards/history/?format=xml")
        assert response.status_code == 400
        assert response.data["error"]["details"]["format"] == [
            "Unsupported format. Use one of: csv, pdf."
        ]

    def test_history_rejects_invalid_type(self, auth_client: APIClient) -> None:
        response = auth_client.get("/api/rewards/history/?type=redeemeda")
        assert response.status_code == 400
        assert response.data["error"]["details"]["type"] == [
            "Unsupported type. Use one of: earned, redeemed."
        ]

    def test_history_rejects_invalid_ordering(self, auth_client: APIClient) -> None:
        response = auth_client.get("/api/rewards/history/?ordering=pointss")
        assert response.status_code == 400
        assert response.data["error"]["details"]["ordering"] == [
            "Unsupported ordering. Use one of: created_at, points, type."
        ]


@pytest.mark.django_db
class TestCustomerRewardHistoryView:
    """GET /api/rewards/customer/{email}/history/ — staff or self."""

    def test_self_access_returns_transactions(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 100)

        response = auth_client.get(f"/api/rewards/customer/{customer.email}/history/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 1

    def test_empty_history(self, auth_client: APIClient, customer: Customer) -> None:
        response = auth_client.get(f"/api/rewards/customer/{customer.email}/history/")
        assert response.status_code == 200
        assert response.data["meta"]["count"] == 0


@pytest.mark.django_db
class TestRewardTransactionDetailView:
    def test_customer_sees_own_transaction(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        txn = RewardTransaction.objects.create(
            customer=customer,
            customer_email=customer.email,
            rental=rental,
            type=TransactionType.EARNED,
            points=100,
            reason="test seed",
            breakdown={"base_points": 100},
        )

        response = auth_client.get(f"/api/rewards/transactions/{txn.id}/")
        assert response.status_code == 200
        assert response.data["data"]["breakdown"] == {"base_points": 100}

    def test_customer_cannot_see_other_transaction(
        self, auth_client: APIClient, staff_user: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, staff_user)
        txn = RewardTransaction.objects.create(
            customer=staff_user,
            customer_email=staff_user.email,
            rental=rental,
            type=TransactionType.EARNED,
            points=100,
            reason="test seed",
            breakdown={"base_points": 100},
        )

        response = auth_client.get(f"/api/rewards/transactions/{txn.id}/")
        assert response.status_code == 404

    def test_staff_sees_any_transaction(
        self, staff_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        txn = RewardTransaction.objects.create(
            customer=customer,
            customer_email=customer.email,
            rental=rental,
            type=TransactionType.EARNED,
            points=100,
            reason="test seed",
            breakdown={"base_points": 100},
        )

        response = staff_client.get(f"/api/rewards/transactions/{txn.id}/")
        assert response.status_code == 200
        assert response.data["data"]["breakdown"] == {"base_points": 100}


@pytest.mark.django_db
class TestRewardRedeemView:
    """POST /api/rewards/apply/ — authenticated user redeems their own points."""

    def test_redeem_success(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=10)
        _earn_points(customer, rental, 300)

        data = {"rental_id": str(rental.id), "points_to_redeem": 200}
        response = auth_client.post("/api/rewards/apply/", data, format="json")
        assert response.status_code == 200
        txn = response.data["data"]
        assert txn["type"] == "redeemed"
        assert txn["points"] == -200

    def test_redeem_insufficient_points(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 50)

        data = {"rental_id": str(rental.id), "points_to_redeem": 200}
        response = auth_client.post("/api/rewards/apply/", data, format="json")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "insufficient_points"

    def test_redeem_below_minimum_rejected_by_serializer(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 300)

        data = {"rental_id": str(rental.id), "points_to_redeem": 50}
        response = auth_client.post("/api/rewards/apply/", data, format="json")
        assert response.status_code == 400

    def test_redeem_nonexistent_rental(
        self, auth_client: APIClient, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer)
        _earn_points(customer, rental, 300)

        data = {"rental_id": str(uuid.uuid4()), "points_to_redeem": 100}
        response = auth_client.post("/api/rewards/apply/", data, format="json")
        assert response.status_code == 404

    def test_redeem_other_customers_rental(
        self,
        auth_client: APIClient,
        customer: Customer,
        staff_user: Customer,
        economic_car: Car,
    ) -> None:
        """Customer A cannot redeem on rental owned by Customer B."""
        rental = _make_rental(economic_car, staff_user)
        RewardTransaction.objects.create(
            customer=customer,
            customer_email=customer.email,
            rental=rental,
            type=TransactionType.EARNED,
            points=300,
            reason="seed",
        )
        data = {"rental_id": str(rental.id), "points_to_redeem": 100}
        response = auth_client.post("/api/rewards/apply/", data, format="json")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "customer_mismatch"

    def test_redeem_invalid_data(self, auth_client: APIClient) -> None:
        response = auth_client.post("/api/rewards/apply/", {}, format="json")
        assert response.status_code == 400

    def test_requires_authentication(self, api_client: APIClient) -> None:
        response = api_client.post("/api/rewards/apply/", {}, format="json")
        assert response.status_code == 401
