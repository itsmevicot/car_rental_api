"""Shared exception base classes."""

from rest_framework import status


class ServiceError(Exception):
    """Base class for all service-layer exceptions."""

    code: str = "service_error"
    message: str = "An error occurred."
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None) -> None:
        """Initialize the exception payload.

        Args:
            message: Optional override for the default message.
        """
        self.message = message or self.__class__.message
        super().__init__(self.message)


class NotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""

    code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, resource: str, identifier=None) -> None:
        """Build a not-found error for a domain resource.

        Args:
            resource: Human-readable resource name.
            identifier: Optional missing identifier.
        """
        msg = f"{resource} not found" if identifier is None else f"{resource} not found"
        super().__init__(msg)


class AuthorizationError(ServiceError):
    """Raised when the caller lacks permission for an operation."""

    code = "permission_denied"
    message = "You do not have permission to access this resource."
    status_code = status.HTTP_403_FORBIDDEN
