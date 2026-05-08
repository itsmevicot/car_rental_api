"""Tests for rewards-specific exceptions."""

from rewards.exceptions import (
    CustomerMismatchError,
    InsufficientPointsError,
    MinimumRedemptionError,
)


def test_insufficient_points_stores_attributes() -> None:
    err = InsufficientPointsError(50, 200)
    assert err.available == 50
    assert err.requested == 200
    assert err.code == "insufficient_points"


def test_minimum_redemption() -> None:
    err = MinimumRedemptionError()
    assert err.code == "minimum_redemption"
    assert "100" in err.message


def test_customer_mismatch() -> None:
    err = CustomerMismatchError()
    assert err.code == "customer_mismatch"
