"""Serializers for the cars domain."""

from rest_framework import serializers

from cars.models import Car


class CarSerializer(serializers.ModelSerializer):
    category = serializers.CharField(read_only=True)

    class Meta:
        model = Car
        fields = (
            "id",
            "brand",
            "model",
            "year",
            "daily_rate",
            "available",
            "category",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
