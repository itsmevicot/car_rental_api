"""Tests for customer repository helpers."""

import pytest
from django.db import transaction

from customers.models import Customer
from customers.repositories import CustomerRepository


def test_customer_repository_roundtrip(customer: Customer) -> None:
    repo = CustomerRepository()
    assert repo.get_by_email("JOHN@example.com") == customer
    assert repo.get_by_id(customer.id) == customer
    assert repo.none().count() == 0


@pytest.mark.django_db
def test_customer_repository_create_user() -> None:
    repo = CustomerRepository()
    user = repo.create_user(email="repo@example.com", password="secret123")
    assert user.email == "repo@example.com"
    assert user.check_password("secret123")


def test_customer_repository_for_update(customer: Customer) -> None:
    repo = CustomerRepository()
    with transaction.atomic():
        assert repo.get_by_id_for_update(customer.id) == customer
        assert repo.get_by_email_for_update(customer.email) == customer
