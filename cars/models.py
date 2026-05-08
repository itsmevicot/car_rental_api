"""Car fleet model."""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from uuid_extensions import uuid7


class CarCategory(models.TextChoices):
    ECONOMIC = "economic", "Economic"
    STANDARD = "standard", "Standard"
    PREMIUM = "premium", "Premium"


class Car(models.Model):
    """A car available for rental."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cars"
        ordering = ["brand", "model"]

    @property
    def category(self) -> str:
        """Derived category based on daily_rate."""
        if self.daily_rate >= Decimal("500"):
            return CarCategory.PREMIUM
        if self.daily_rate >= Decimal("300"):
            return CarCategory.STANDARD
        return CarCategory.ECONOMIC

    def __str__(self) -> str:
        return f"{self.brand} {self.model} ({self.year})"
