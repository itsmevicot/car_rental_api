"""Shared view mixins."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet


class CustomerScopedQuerysetMixin:
    """Scope list querysets: staff sees all, customers see only their own records."""

    request: Any

    def scope_queryset_to_customer(self, queryset: QuerySet) -> QuerySet:
        """Restrict a queryset to the authenticated customer when needed.

        Args:
            queryset: Base queryset to scope.

        Returns:
            QuerySet: Original queryset for staff users, otherwise customer-scoped queryset.
        """
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(customer=user)
