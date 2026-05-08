"""Customer test support helpers."""

from customers.models import Customer


def create_customer() -> Customer:
    """Create the default authenticated customer used in tests.

    Returns:
        Customer: Persisted regular customer instance.
    """
    return Customer.objects.create_user(
        email="john@example.com",
        password="testpass123",
        first_name="John",
        last_name="Doe",
    )


def create_staff_user() -> Customer:
    """Create the default staff user used in tests.

    Returns:
        Customer: Persisted staff customer instance.
    """
    return Customer.objects.create_user(
        email="admin@example.com",
        password="testpass123",
        is_staff=True,
    )
