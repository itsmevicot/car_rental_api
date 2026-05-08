"""Customer test fixtures."""

import pytest
from rest_framework.test import APIClient

from customers.models import Customer
from customers.tests.support import create_customer, create_staff_user


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def customer(db) -> Customer:
    """Create a regular customer."""
    return create_customer()


@pytest.fixture
def customer_email(customer: Customer) -> str:
    """Return the default customer email."""
    return customer.email


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
