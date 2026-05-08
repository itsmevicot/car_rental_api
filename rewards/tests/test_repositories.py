"""Tests for reward repository helpers."""

from datetime import timedelta

from django.utils import timezone

from rentals.models import Rental
from rewards.models import RewardTransaction, TransactionType
from rewards.repositories import RewardRepository


def _make_rental(customer, economic_car) -> Rental:
    now = timezone.now()
    return Rental.objects.create(
        car=economic_car,
        customer=customer,
        customer_name="John Doe",
        customer_email=customer.email,
        start_date=now,
        end_date=now + timedelta(days=3),
        total_cost=economic_car.daily_rate * 3,
    )


def test_reward_repository_summary_and_history(customer, economic_car) -> None:
    repo = RewardRepository()
    rental = _make_rental(customer, economic_car)
    RewardTransaction.objects.create(
        customer=customer,
        customer_email=customer.email,
        rental=rental,
        type=TransactionType.EARNED,
        points=200,
        reason="earned",
    )
    RewardTransaction.objects.create(
        customer=customer,
        customer_email=customer.email,
        rental=rental,
        type=TransactionType.REDEEMED,
        points=-100,
        reason="redeemed",
    )

    summary = repo.get_summary_for_customer(customer)
    assert summary == {
        "lifetime_points_earned": 200,
        "lifetime_points_redeemed": 100,
        "total_points": 100,
    }
    assert repo.get_history_for_customer(customer).count() == 2
    assert repo.get_history_by_email(customer.email).count() == 2
