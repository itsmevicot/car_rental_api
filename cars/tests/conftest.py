"""Car test fixtures."""

import pytest
from rest_framework.test import APIClient

from cars.models import Car
from cars.tests.support import (
    create_economic_car,
    create_premium_car,
    create_standard_car,
    create_unavailable_car,
)
from customers.models import Customer
from customers.tests.support import create_customer, create_staff_user


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def customer(db) -> Customer:
    """Create a regular authenticated customer."""
    return create_customer()


@pytest.fixture
def staff_user(db) -> Customer:
    """Create a staff user."""
    return create_staff_user()


@pytest.fixture
def authenticated_client(customer: Customer) -> APIClient:
    """Return an API client authenticated as a regular customer."""
    client = APIClient()
    client.force_authenticate(user=customer)
    return client


@pytest.fixture
def staff_client(staff_user: Customer) -> APIClient:
    """Return an API client authenticated as a staff user."""
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture
def economic_car(db) -> Car:
    """Create an economic category car."""
    return create_economic_car()


@pytest.fixture
def standard_car(db) -> Car:
    """Create a standard category car."""
    return create_standard_car()


@pytest.fixture
def premium_car(db) -> Car:
    """Create a premium category car."""
    return create_premium_car()


@pytest.fixture
def unavailable_car(db) -> Car:
    """Create an unavailable car."""
    return create_unavailable_car()
