"""Tests for reward transaction model helpers."""

from rewards.models import RewardTransaction


def test_reward_transaction_str(customer, economic_car) -> None:
    from rentals.models import Rental

    rental = Rental.objects.create(
        car=economic_car,
        customer=customer,
        customer_name="John Doe",
        customer_email=customer.email,
        start_date="2026-01-01T00:00:00Z",
        end_date="2026-01-02T00:00:00Z",
        total_cost="50.00",
    )
    txn = RewardTransaction.objects.create(
        customer=customer,
        customer_email=customer.email,
        rental=rental,
        type="earned",
        points=100,
        reason="seed",
    )
    assert str(txn) == f"earned 100pts — {customer.email}"
