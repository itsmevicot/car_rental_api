"""Business logic for the cars domain."""

from uuid import UUID

from django.db.models import QuerySet

from cars.models import Car
from cars.repositories import CarRepository
from core.exceptions import NotFoundError


class CarService:
    """Coordinate car-related operations."""

    def __init__(self, repo: CarRepository | None = None) -> None:
        self._repo = repo or CarRepository()

    def list_all(self) -> QuerySet[Car]:
        """Return the complete fleet.

        Returns:
            QuerySet[Car]: All cars regardless of availability.
        """
        return self._repo.list_all()

    def list_available(self) -> QuerySet[Car]:
        """Return available cars.

        Returns:
            QuerySet[Car]: Available cars ready to be listed.
        """
        return self._repo.list_available()

    def empty_list(self) -> QuerySet[Car]:
        """Return an empty car queryset.

        Returns:
            QuerySet[Car]: Empty queryset used by schema generation flows.
        """
        return self._repo.none()

    def get_by_id(self, car_id: UUID) -> Car:
        """Return a car by identifier regardless of availability.

        Args:
            car_id: Target car identifier.

        Returns:
            Car: Matching car instance.

        Raises:
            NotFoundError: If the car does not exist.
        """
        car = self._repo.get_by_id(car_id)
        if car is None:
            raise NotFoundError("Car", car_id)
        return car

    def get_available_by_id(self, car_id: UUID) -> Car:
        """Return an available car by identifier.

        Args:
            car_id: Target car identifier.

        Returns:
            Car: Matching available car instance.

        Raises:
            NotFoundError: If the car does not exist or is unavailable.
        """
        car = self._repo.get_available_by_id(car_id)
        if car is None:
            raise NotFoundError("Car", car_id)
        return car
