"""Serializers for the rentals domain."""

from rest_framework import serializers

from rentals.models import Rental


class RentalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = (
            "id",
            "car",
            "customer_name",
            "customer_email",
            "start_date",
            "end_date",
            "subtotal",
            "duration_discount",
            "reward_discount",
            "total_cost",
            "returned",
            "actual_return_date",
            "late_fee",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class RentalCreateSerializer(serializers.Serializer):
    car_id = serializers.UUIDField()
    customer_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional display name snapshot stored on the rental.",
    )
    customer_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Optional customer email. For non-staff users, this must match the JWT user.",
    )
    days = serializers.IntegerField(min_value=1)


class RentalStatsSerializer(serializers.Serializer):
    total_rentals = serializers.IntegerField()
    active_rentals = serializers.IntegerField()
    total_revenue = serializers.CharField()
    total_cars = serializers.IntegerField()
    available_cars = serializers.IntegerField()
