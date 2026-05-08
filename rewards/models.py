"""Reward transaction ledger model."""

from __future__ import annotations

from django.db import models
from uuid_extensions import uuid7

from customers.models import Customer
from rentals.models import Rental


class CustomerTier(models.TextChoices):
    BRONZE = "Bronze", "Bronze"
    SILVER = "Silver", "Silver"
    GOLD = "Gold", "Gold"


class TransactionType(models.TextChoices):
    EARNED = "earned", "Earned"
    REDEEMED = "redeemed", "Redeemed"


class RewardTransaction(models.Model):
    """Append-only ledger entry."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="reward_transactions"
    )
    customer_email = models.EmailField(db_index=True)
    rental = models.ForeignKey(
        "rentals.Rental", on_delete=models.PROTECT, related_name="reward_transactions"
    )
    type = models.CharField(max_length=8, choices=TransactionType.choices)
    points = models.IntegerField()
    reason = models.CharField(max_length=255)
    breakdown = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reward_transactions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.type} {self.points}pts — {self.customer_email}"
