"""Tests for customer serializers."""

import pytest

from customers.serializers import CustomerRegistrationSerializer


@pytest.mark.django_db
def test_customer_registration_serializer_create() -> None:
    serializer = CustomerRegistrationSerializer(
        data={
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "secret123",
        }
    )
    assert serializer.is_valid(), serializer.errors
    customer = serializer.save()
    assert customer.email == "new@example.com"
    assert customer.check_password("secret123")
