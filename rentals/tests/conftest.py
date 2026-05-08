"""Rental test fixtures."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from cars.models import Car
from cars.tests.support import create_economic_car, create_unavailable_car
from customers.models import Customer
from customers.tests.support import create_customer, create_staff_user
from rentals.models import Rental


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def customer(db) -> Customer:
    """Create a regular customer."""
    return create_customer()


@pytest.fixture
def staff_user(db) -> Customer:
    """Create a staff user."""
    return create_staff_user()


@pytest.fixture
def auth_client(api_client: APIClient, customer: Customer) -> APIClient:
    """Return an authenticated customer client."""
    api_client.force_authenticate(user=customer)
    return api_client


@pytest.fixture
def staff_client(api_client: APIClient, staff_user: Customer) -> APIClient:
    """Return an authenticated staff client."""
    api_client.force_authenticate(user=staff_user)
    return api_client


@pytest.fixture
def economic_car(db) -> Car:
    """Create an economic category car."""
    return create_economic_car()


@pytest.fixture
def unavailable_car(db) -> Car:
    """Create an unavailable car."""
    return create_unavailable_car()


@pytest.fixture
def active_rental(economic_car: Car, customer: Customer) -> Rental:
    """Create an active rental."""
    now = timezone.now()
    return Rental.objects.create(
        car=economic_car,
        customer=customer,
        customer_name="John Doe",
        customer_email=customer.email,
        start_date=now - timedelta(days=3),
        end_date=now + timedelta(days=2),
        total_cost=Decimal("250.00"),
    )


@pytest.fixture
def returned_rental(economic_car: Car, customer: Customer) -> Rental:
    """Create a returned rental."""
    now = timezone.now()
    return Rental.objects.create(
        car=economic_car,
        customer=customer,
        customer_name="John Doe",
        customer_email=customer.email,
        start_date=now - timedelta(days=5),
        end_date=now - timedelta(days=1),
        total_cost=Decimal("250.00"),
        returned=True,
        actual_return_date=now - timedelta(days=1),
    )
