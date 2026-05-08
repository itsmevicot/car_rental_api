"""Domain exceptions for the rentals app."""

from rest_framework import status

from core.exceptions import ServiceError


class CarNotAvailableError(ServiceError):
    code = "car_not_available"
    message = "Car is not available for rental"
    status_code = status.HTTP_400_BAD_REQUEST


class RentalAlreadyReturnedError(ServiceError):
    code = "rental_already_returned"
    message = "Car has already been returned"
    status_code = status.HTTP_400_BAD_REQUEST
