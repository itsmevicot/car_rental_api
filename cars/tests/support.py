"""Car test support helpers."""

from decimal import Decimal

from cars.models import Car


def create_economic_car() -> Car:
    """Create the default economic category car.

    Returns:
        Car: Persisted economic car instance.
    """
    return Car.objects.create(
        brand="Toyota",
        model="Corolla",
        year=2020,
        daily_rate=Decimal("50.00"),
    )


def create_standard_car() -> Car:
    """Create the default standard category car.

    Returns:
        Car: Persisted standard car instance.
    """
    return Car.objects.create(
        brand="Audi",
        model="A3",
        year=2023,
        daily_rate=Decimal("350.00"),
    )


def create_premium_car() -> Car:
    """Create the default premium category car.

    Returns:
        Car: Persisted premium car instance.
    """
    return Car.objects.create(
        brand="Audi",
        model="Q3",
        year=2023,
        daily_rate=Decimal("600.00"),
    )


def create_unavailable_car() -> Car:
    """Create the default unavailable car.

    Returns:
        Car: Persisted unavailable car instance.
    """
    return Car.objects.create(
        brand="Honda",
        model="Civic",
        year=2021,
        daily_rate=Decimal("55.00"),
        available=False,
    )
