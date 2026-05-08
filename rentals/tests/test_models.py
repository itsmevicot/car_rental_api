"""Tests for rental model helpers."""

from decimal import Decimal

from rentals.models import Rental


def test_rental_ensure_pricing_breakdown_backfills(active_rental: Rental) -> None:
    active_rental.subtotal = None
    active_rental.duration_discount = None
    active_rental.reward_discount = None
    active_rental.ensure_pricing_breakdown()
    assert active_rental.subtotal == active_rental.total_cost
    assert active_rental.duration_discount == Decimal("0.00")
    assert active_rental.reward_discount == Decimal("0.00")


def test_rental_ensure_pricing_breakdown_keeps_existing_values(active_rental: Rental) -> None:
    active_rental.subtotal = Decimal("1.00")
    active_rental.duration_discount = Decimal("2.00")
    active_rental.reward_discount = Decimal("3.00")
    original_subtotal = active_rental.subtotal
    original_duration_discount = active_rental.duration_discount
    original_reward_discount = active_rental.reward_discount
    active_rental.ensure_pricing_breakdown()
    assert active_rental.subtotal == original_subtotal
    assert active_rental.duration_discount == original_duration_discount
    assert active_rental.reward_discount == original_reward_discount


def test_rental_str(active_rental: Rental) -> None:
    assert str(active_rental) == f"Rental {active_rental.id} — {active_rental.customer_email}"
