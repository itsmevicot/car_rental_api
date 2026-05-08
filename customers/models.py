"""Custom user model using email as the login identifier."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from uuid_extensions import uuid7


class CustomerManager(BaseUserManager):
    """Manager that uses email instead of username."""

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any):
        """Create and return a regular customer user.

        Args:
            email: Email used as the login identifier.
            password: Raw password to hash for the user.
            **extra_fields: Additional fields to persist on the user.

        Returns:
            Customer: Newly created customer user.

        Raises:
            ValueError: If the email is missing.
        """
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any):
        """Create and return a superuser.

        Args:
            email: Email used as the login identifier.
            password: Raw password to hash for the user.
            **extra_fields: Additional fields to persist on the user.

        Returns:
            Customer: Newly created superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Customer(AbstractUser):
    """Customer account — email is the login identifier, UUID v7 primary key."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomerManager()

    class Meta:
        db_table = "customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self) -> str:
        return self.email
