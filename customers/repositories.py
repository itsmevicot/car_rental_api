"""Data-access layer for the customers domain."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

Customer = get_user_model()


class CustomerRepository:
    """Persist and fetch customer records."""

    def create_user(self, **kwargs: Any):
        """Create and return a customer user.

        Args:
            **kwargs: User creation payload accepted by the custom manager.

        Returns:
            Any: Created customer instance.
        """
        return Customer.objects.create_user(**kwargs)

    def get_by_email(self, email: str):
        """Return a customer matched by email.

        Args:
            email: Customer email to search for.

        Returns:
            Any: Matching customer when found, otherwise ``None``.
        """
        return Customer.objects.filter(email__iexact=email).first()

    def get_by_id(self, customer_id: UUID):
        """Return a customer by primary key.

        Args:
            customer_id: Customer identifier.

        Returns:
            Any: Matching customer when found, otherwise ``None``.
        """
        return Customer.objects.filter(id=customer_id).first()

    def get_by_id_for_update(self, customer_id: UUID):
        """Lock and return a customer by primary key.

        Args:
            customer_id: Customer identifier.

        Returns:
            Any: Matching locked customer when found, otherwise ``None``.
        """
        return Customer.objects.select_for_update().filter(id=customer_id).first()

    def get_by_email_for_update(self, email: str):
        """Lock and return a customer matched by email.

        Args:
            email: Customer email to search for.

        Returns:
            Any: Matching locked customer when found, otherwise ``None``.
        """
        return Customer.objects.select_for_update().filter(email__iexact=email).first()

    def none(self) -> QuerySet:
        """Return an empty customer queryset.

        Returns:
            QuerySet: Empty queryset for customer records.
        """
        return Customer.objects.none()
