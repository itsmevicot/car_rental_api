"""Domain exceptions for the rewards app."""

from rest_framework import status

from core.exceptions import ServiceError


class InsufficientPointsError(ServiceError):
    code = "insufficient_points"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, available: int, requested: int) -> None:
        self.available = available
        self.requested = requested
        super().__init__(f"Insufficient points: {available} available, {requested} requested")


class MinimumRedemptionError(ServiceError):
    code = "minimum_redemption"
    message = "Minimum redemption is 100 points"
    status_code = status.HTTP_400_BAD_REQUEST


class CustomerMismatchError(ServiceError):
    code = "customer_mismatch"
    message = "Customer email does not match the rental"
    status_code = status.HTTP_400_BAD_REQUEST
