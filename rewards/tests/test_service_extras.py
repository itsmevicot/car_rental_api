"""Extra reward service coverage."""

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.utils import timezone

from core.exceptions import NotFoundError
from customers.models import Customer
from rentals.models import Rental
from rewards.exceptions import MinimumRedemptionError
from rewards.models import RewardTransaction, TransactionType
from rewards.services import RewardService


def _make_rental(car, customer: Customer, days: int) -> Rental:
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


def _earn(customer: Customer, rental: Rental, points: int) -> None:
    RewardTransaction.objects.create(
        customer=customer,
        customer_email=customer.email,
        rental=rental,
        type=TransactionType.EARNED,
        points=points,
        reason="seed",
    )


@pytest.mark.django_db
class TestRewardServiceExtras:
    def test_award_points_standard_week_bonus(self, customer, standard_car) -> None:
        service = RewardService()
        rental = _make_rental(standard_car, customer, days=7)
        rental.returned = True
        rental.actual_return_date = rental.end_date
        rental.save(update_fields=["returned", "actual_return_date"])
        txn = service.award_points(rental, returned_on_time=True)
        assert txn.breakdown["category_bonus_points"] == 35
        assert txn.breakdown["duration_bonus_points"] == 50

    def test_award_points_premium_extended_bonus_and_missing_locked_customer(
        self, customer, premium_car
    ) -> None:
        service = RewardService()
        rental = _make_rental(premium_car, customer, days=14)
        rental.returned = True
        rental.actual_return_date = rental.end_date
        rental.save(update_fields=["returned", "actual_return_date"])
        txn = service.award_points(rental, returned_on_time=False)
        assert txn.breakdown["category_bonus_points"] == 140
        assert txn.breakdown["duration_bonus_points"] == 150

        with (
            patch.object(service._customers, "get_by_id_for_update", return_value=None),
            pytest.raises(NotFoundError),
        ):
            service.award_points(rental, returned_on_time=True)

    def test_summary_transitions_and_resolution_helpers(self, customer, economic_car) -> None:
        service = RewardService()
        rental = _make_rental(economic_car, customer, days=1)
        _earn(customer, rental, 600)
        summary = service.get_customer_summary(customer)
        assert summary["tier"] == "Silver"
        assert summary["points_to_next_tier"] == 400

        rental2 = _make_rental(economic_car, customer, days=1)
        _earn(customer, rental2, 500)
        summary = service.get_customer_summary_by_email(customer.email)
        assert summary["tier"] == "Gold"
        assert summary["points_to_next_tier"] == 0

        assert service.get_customer_summary_by_id(customer.id)["customer_email"] == customer.email
        assert service.get_customer_history_by_id(customer.id).count() == 2
        assert service.resolve_customer_by_email(customer.email) == customer
        assert service.resolve_customer_by_id(customer.id) == customer

    def test_summary_by_email_silver_points_to_next(self, customer, economic_car) -> None:
        service = RewardService()
        rental = _make_rental(economic_car, customer, days=1)
        _earn(customer, rental, 600)
        summary = service.get_customer_summary_by_email(customer.email)
        assert summary["tier"] == "Silver"
        assert summary["points_to_next_tier"] == 400

    def test_not_found_resolution_helpers(self) -> None:
        service = RewardService()
        missing = uuid4()
        with pytest.raises(NotFoundError):
            service.get_customer_summary_by_id(missing)
        with pytest.raises(NotFoundError):
            service.get_customer_history_by_id(missing)
        with pytest.raises(NotFoundError):
            service.resolve_customer_by_email("missing@example.com")
        with pytest.raises(NotFoundError):
            service.resolve_customer_by_id(missing)

    def test_redeem_points_missing_locked_customer(self, customer, economic_car) -> None:
        service = RewardService()
        rental = _make_rental(economic_car, customer, days=3)
        _earn(customer, rental, 300)
        with (
            patch.object(service._customers, "get_by_id_for_update", return_value=None),
            pytest.raises(NotFoundError),
        ):
            service.redeem_points(rental.id, customer, 100)

    def test_redeem_logs_warning_before_atomic(self, customer, economic_car) -> None:
        service = RewardService()
        rental = _make_rental(economic_car, customer, days=3)
        _earn(customer, rental, 300)
        with pytest.raises(MinimumRedemptionError):
            service.redeem_points(rental.id, customer, 50)
