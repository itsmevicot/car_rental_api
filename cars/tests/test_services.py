"""Tests for car services."""

import uuid

import pytest

from cars.services import CarService
from core.exceptions import NotFoundError


@pytest.mark.django_db
class TestCarService:
    def test_get_by_id_raises_not_found_for_missing_car(self) -> None:
        service = CarService()

        with pytest.raises(NotFoundError):
            service.get_by_id(uuid.uuid4())
