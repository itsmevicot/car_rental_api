"""Serializers for customer registration and profile."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from customers.repositories import CustomerRepository

Customer = get_user_model()
_customers = CustomerRepository()


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password used to register and obtain JWT tokens.",
    )

    class Meta:
        model = Customer
        fields = ("email", "first_name", "last_name", "password")

    def create(self, validated_data):
        return _customers.create_user(**validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "email", "first_name", "last_name")
        read_only_fields = fields
