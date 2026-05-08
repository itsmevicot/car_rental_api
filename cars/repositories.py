"""Data-access layer for the cars domain."""

from uuid import UUID

from django.db.models import Count, Q, QuerySet

from cars.models import Car


class CarRepository:
    """Persist and fetch car records."""

    def list_all(self) -> QuerySet[Car]:
        """Return all cars regardless of availability.

        Returns:
            QuerySet[Car]: Queryset containing the full fleet.
        """
        return Car.objects.all()

    def list_available(self) -> QuerySet[Car]:
        """Return cars that are currently available for rental.

        Returns:
            QuerySet[Car]: Queryset containing only available cars.
        """
        return Car.objects.filter(available=True)

    def get_by_id(self, car_id: UUID) -> Car | None:
        """Return a car by its identifier.

        Args:
            car_id: Target car identifier.

        Returns:
            Car | None: Matching car when found, otherwise ``None``.
        """
        return Car.objects.filter(id=car_id).first()

    def get_available_by_id(self, car_id: UUID) -> Car | None:
        """Return an available car by its identifier.

        Args:
            car_id: Target car identifier.

        Returns:
            Car | None: Matching available car when found, otherwise ``None``.
        """
        return Car.objects.filter(id=car_id, available=True).first()

    def get_by_id_for_update(self, car_id: UUID) -> Car | None:
        """Lock and return a car by its identifier.

        Args:
            car_id: Target car identifier.

        Returns:
            Car | None: Matching locked car when found, otherwise ``None``.
        """
        return Car.objects.select_for_update().filter(id=car_id).first()

    def update_availability(self, car: Car, *, available: bool) -> None:
        """Persist a car availability change.

        Args:
            car: Car instance to update.
            available: New availability flag to persist.
        """
        car.available = available
        car.save(update_fields=["available", "updated_at"])

    def aggregate_counts(self) -> dict:
        """Return aggregate car metrics.

        Returns:
            dict: Aggregate totals for the fleet.
        """
        return Car.objects.aggregate(
            total_cars=Count("id"),
            available_cars=Count("id", filter=Q(available=True)),
        )

    def none(self) -> QuerySet[Car]:
        """Return an empty car queryset.

        Returns:
            QuerySet[Car]: Empty queryset for swagger and fallback flows.
        """
        return Car.objects.none()
