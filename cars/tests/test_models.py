"""Tests for car model helpers."""

from cars.models import Car


def test_car_str(economic_car: Car) -> None:
    """Car string representation should be stable and descriptive."""
    assert str(economic_car) == "Toyota Corolla (2020)"
