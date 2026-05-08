"""Extra reward view coverage."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from rentals.models import Rental
from rewards.models import RewardTransaction, TransactionType
from rewards.views import CustomerRewardHistoryByIdView


def _make_rental(customer, car, days: int = 3) -> Rental:
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


def _earn(customer, rental, points: int) -> RewardTransaction:
    return RewardTransaction.objects.create(
        customer=customer,
        customer_email=customer.email,
        rental=rental,
        type=TransactionType.EARNED,
        points=points,
        reason="seed",
    )


@pytest.mark.django_db
class TestRewardViewExtras:
    def test_history_exports(self, auth_client, customer, economic_car) -> None:
        rental = _make_rental(customer, economic_car)
        _earn(customer, rental, 100)

        csv_response = auth_client.get("/api/rewards/history/?format=csv")
        assert csv_response.status_code == 200
        assert csv_response["Content-Type"] == "text/csv"
        assert "rewards_john@example.com.csv" in csv_response["Content-Disposition"]

        pdf_response = auth_client.get("/api/rewards/history/?format=pdf")
        assert pdf_response.status_code == 200
        assert pdf_response["Content-Type"] == "application/pdf"

    def test_history_pdf_export_handles_page_break(
        self, auth_client, customer, economic_car
    ) -> None:
        rental = _make_rental(customer, economic_car)
        for _ in range(41):
            _earn(customer, rental, 100)

        response = auth_client.get("/api/rewards/history/?format=pdf")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

    def test_customer_email_history_exports(self, staff_client, customer, economic_car) -> None:
        rental = _make_rental(customer, economic_car)
        _earn(customer, rental, 100)

        csv_response = staff_client.get(
            f"/api/rewards/customer/{customer.email}/history/?format=csv"
        )
        assert csv_response.status_code == 200
        pdf_response = staff_client.get(
            f"/api/rewards/customer/{customer.email}/history/?format=pdf"
        )
        assert pdf_response.status_code == 200

    def test_customer_id_views_and_exports(self, staff_client, customer, economic_car) -> None:
        rental = _make_rental(customer, economic_car)
        _earn(customer, rental, 100)

        summary = staff_client.get(f"/api/rewards/customers/{customer.id}/")
        assert summary.status_code == 200
        history = staff_client.get(f"/api/rewards/customers/{customer.id}/history/")
        assert history.status_code == 200
        csv_response = staff_client.get(f"/api/rewards/customers/{customer.id}/history/?format=csv")
        assert csv_response.status_code == 200
        pdf_response = staff_client.get(f"/api/rewards/customers/{customer.id}/history/?format=pdf")
        assert pdf_response.status_code == 200

    def test_customer_id_history_get_queryset_fallback(self, customer, economic_car) -> None:
        rental = _make_rental(customer, economic_car)
        _earn(customer, rental, 100)
        view = CustomerRewardHistoryByIdView()
        view.request = APIRequestFactory().get("/api/rewards/history/")
        view.kwargs = {"customer_id": str(customer.id)}
        queryset = view.get_queryset()
        assert queryset.count() == 1

    def test_staff_redeem_branch(self, staff_client, customer, economic_car) -> None:
        rental = _make_rental(customer, economic_car, days=10)
        _earn(customer, rental, 300)
        response = staff_client.post(
            "/api/rewards/apply/",
            {
                "rental_id": str(rental.id),
                "customer_email": customer.email,
                "points_to_redeem": 200,
            },
            format="json",
        )
        assert response.status_code == 200
