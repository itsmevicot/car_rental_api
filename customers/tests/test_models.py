"""Tests for the customer model and manager."""

import pytest

from customers.models import Customer


@pytest.mark.django_db
class TestCustomerManager:
    def test_create_user_requires_email(self) -> None:
        with pytest.raises(ValueError):
            Customer.objects.create_user(email="", password="secret123")

    def test_create_superuser_sets_flags(self) -> None:
        user = Customer.objects.create_superuser("admin@rental.com", "admin12345")
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_customer_str_returns_email(self, customer: Customer) -> None:
        assert str(customer) == "john@example.com"
