"""Rental model."""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from uuid_extensions import uuid7

from customers.models import Customer


class Rental(models.Model):
    """A car rental transaction."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    car = models.ForeignKey("cars.Car", on_delete=models.PROTECT, related_name="rentals")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="rentals")
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(db_index=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    duration_discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    reward_discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    returned = models.BooleanField(default=False)
    actual_return_date = models.DateTimeField(null=True, blank=True)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rentals"
        ordering = ["-created_at"]

    def ensure_pricing_breakdown(self) -> None:
        """Backfill pricing fields for rows created before breakdown fields existed."""
        if self.subtotal:
            return
        self.subtotal = self.total_cost
        self.duration_discount = Decimal("0.00")
        self.reward_discount = Decimal("0.00")

    def calculate_total_cost(self) -> Decimal:
        """Recalculate the total considering all discounts and late fee."""
        total = self.subtotal - self.duration_discount - self.reward_discount
        total += self.late_fee or Decimal("0.00")
        return max(Decimal("0.00"), total)

    def __str__(self) -> str:
        return f"Rental {self.id} — {self.customer_email}"
