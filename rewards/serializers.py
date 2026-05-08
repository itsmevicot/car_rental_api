"""Serializers for the rewards domain."""

from rest_framework import serializers

from rewards.constants import (
    ALLOWED_EXPORT_FORMATS,
    ALLOWED_ORDERING,
    ALLOWED_TYPES,
    MIN_REDEEM_POINTS,
)
from rewards.models import RewardTransaction


class RewardSummarySerializer(serializers.Serializer):
    customer_email = serializers.EmailField(help_text="Customer identifier used in the rewards UI.")
    total_points = serializers.IntegerField(help_text="Current available balance.")
    tier = serializers.CharField(help_text="Current loyalty tier.")
    points_to_next_tier = serializers.IntegerField(
        help_text="Lifetime earned points required to reach the next tier."
    )
    lifetime_points_earned = serializers.IntegerField(help_text="All earned points to date.")
    lifetime_points_redeemed = serializers.IntegerField(help_text="All redeemed points to date.")


class RewardTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardTransaction
        fields = ("id", "type", "points", "reason", "rental_id", "created_at")
        read_only_fields = fields


class RewardTransactionDetailSerializer(RewardTransactionSerializer):
    breakdown = serializers.JSONField(read_only=True)

    class Meta(RewardTransactionSerializer.Meta):
        fields = RewardTransactionSerializer.Meta.fields + ("breakdown",)


class HistoryQueryParamsSerializer(serializers.Serializer):
    """Validates and coerces query parameters for history list endpoints."""

    type = serializers.CharField(required=False, allow_blank=True, default=None)
    ordering = serializers.CharField(required=False, allow_blank=True, default=None)
    format = serializers.CharField(required=False, allow_blank=True, default=None)

    def validate_type(self, value: str | None) -> str | None:
        if value and value not in ALLOWED_TYPES:
            opts = ", ".join(sorted(ALLOWED_TYPES))
            raise serializers.ValidationError(f"Unsupported type. Use one of: {opts}.")
        return value or None

    def validate_ordering(self, value: str | None) -> str | None:
        if value:
            normalized = value[1:] if value.startswith("-") else value
            if normalized not in ALLOWED_ORDERING:
                opts = ", ".join(sorted(ALLOWED_ORDERING))
                raise serializers.ValidationError(f"Unsupported ordering. Use one of: {opts}.")
        return value or None

    def validate_format(self, value: str | None) -> str | None:
        if value and value not in ALLOWED_EXPORT_FORMATS:
            opts = ", ".join(sorted(ALLOWED_EXPORT_FORMATS))
            raise serializers.ValidationError(f"Unsupported format. Use one of: {opts}.")
        return value or None


class RewardRedeemSerializer(serializers.Serializer):
    rental_id = serializers.UUIDField(help_text="Rental that will receive the reward discount.")
    customer_email = serializers.EmailField(
        required=False,
        help_text="Required for staff requests redeeming points for another customer.",
    )
    points_to_redeem = serializers.IntegerField(min_value=MIN_REDEEM_POINTS)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_staff and not attrs.get("customer_email"):
            raise serializers.ValidationError(
                {"customer_email": "This field is required when redeeming as staff."}
            )
        return attrs
