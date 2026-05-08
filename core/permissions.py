"""Custom DRF permission classes."""

from rest_framework.permissions import BasePermission

from core.exceptions import AuthorizationError


def assert_customer_email_allowed(request, customer_email: str) -> None:
    """Validate whether the request can access a customer email.

    Args:
        request: Current DRF request.
        customer_email: Target customer email from the route or payload.

    Raises:
        AuthorizationError: If a non-staff user targets another customer email.
    """
    if not request.user.is_staff and request.user.email.lower() != customer_email.lower():
        raise AuthorizationError("You do not have permission to access this customer.")


class IsSelfByEmailOrStaff(BasePermission):
    """Allow access only if the URL email matches the authenticated user, or user is staff."""

    def has_permission(self, request, view):
        """Return whether the request may proceed.

        Args:
            request: Current DRF request.
            view: Current DRF view instance.

        Returns:
            bool: ``True`` when the actor is staff or owns the target email.

        Raises:
            AuthorizationError: If an authenticated non-staff user targets another customer.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        customer_email = view.kwargs.get("customer_email", "")
        if request.user.is_staff:
            return True
        if request.user.email.lower() == customer_email.lower():
            return True
        raise AuthorizationError("You do not have permission to access this customer.")
