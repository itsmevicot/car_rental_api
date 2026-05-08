"""Data-access layer for the rewards domain."""

from __future__ import annotations

from uuid import UUID

from django.db.models import QuerySet, Sum

from rewards.models import RewardTransaction, TransactionType


class RewardRepository:
    """Persist and fetch reward transactions."""

    def create(self, **kwargs) -> RewardTransaction:
        """Create and return a reward transaction.

        Args:
            **kwargs: Reward transaction fields to persist.

        Returns:
            RewardTransaction: Newly created reward transaction.
        """
        return RewardTransaction.objects.create(**kwargs)

    def get_lifetime_earned(self, customer_email: str) -> int:
        """Return lifetime earned points for a customer email.

        Args:
            customer_email: Customer email used as the filter.

        Returns:
            int: Sum of earned points.
        """
        result = RewardTransaction.objects.filter(
            customer_email__iexact=customer_email,
            type=TransactionType.EARNED,
        ).aggregate(total=Sum("points"))
        return result["total"] or 0

    def get_lifetime_earned_for_customer(self, customer) -> int:
        """Return lifetime earned points for a customer instance.

        Args:
            customer: Customer owner of the transactions.

        Returns:
            int: Sum of earned points.
        """
        result = RewardTransaction.objects.filter(
            customer=customer,
            type=TransactionType.EARNED,
        ).aggregate(total=Sum("points"))
        return result["total"] or 0

    def get_lifetime_redeemed(self, customer_email: str) -> int:
        """Return lifetime redeemed points for a customer email.

        Args:
            customer_email: Customer email used as the filter.

        Returns:
            int: Absolute sum of redeemed points.
        """
        result = RewardTransaction.objects.filter(
            customer_email__iexact=customer_email,
            type=TransactionType.REDEEMED,
        ).aggregate(total=Sum("points"))
        return abs(result["total"] or 0)

    def get_lifetime_redeemed_for_customer(self, customer) -> int:
        """Return lifetime redeemed points for a customer instance.

        Args:
            customer: Customer owner of the transactions.

        Returns:
            int: Absolute sum of redeemed points.
        """
        result = RewardTransaction.objects.filter(
            customer=customer,
            type=TransactionType.REDEEMED,
        ).aggregate(total=Sum("points"))
        return abs(result["total"] or 0)

    def get_balance_for_customer(self, customer) -> int:
        """Return current point balance for a customer.

        Args:
            customer: Customer owner of the transactions.

        Returns:
            int: Net point balance.
        """
        result = RewardTransaction.objects.filter(customer=customer).aggregate(total=Sum("points"))
        return result["total"] or 0

    def get_summary_for_customer(self, customer) -> dict:
        """Return a point summary for a customer.

        Args:
            customer: Customer owner of the transactions.

        Returns:
            dict: Summary payload with earned, redeemed, and total points.
        """
        txns = RewardTransaction.objects.filter(customer=customer)
        earned = txns.filter(type=TransactionType.EARNED).aggregate(t=Sum("points"))["t"] or 0
        redeemed = txns.filter(type=TransactionType.REDEEMED).aggregate(t=Sum("points"))["t"] or 0
        return {
            "lifetime_points_earned": earned,
            "lifetime_points_redeemed": abs(redeemed),
            "total_points": earned + redeemed,
        }

    def get_history_for_customer(self, customer) -> QuerySet:
        """Return reward history for a customer.

        Args:
            customer: Customer owner of the transactions.

        Returns:
            QuerySet: Ordered reward transaction history.
        """
        return RewardTransaction.objects.filter(customer=customer).order_by("-created_at")

    def list_by_customer(self, customer) -> QuerySet:
        """Return reward history for a customer.

        Args:
            customer: Customer owner of the transactions.

        Returns:
            QuerySet: Ordered reward transaction history.
        """
        return RewardTransaction.objects.filter(customer=customer).order_by("-created_at")

    def get_history_by_email(self, customer_email: str) -> QuerySet:
        """Return reward history filtered by customer email.

        Args:
            customer_email: Customer email used as the filter.

        Returns:
            QuerySet: Ordered reward transaction history.
        """
        return RewardTransaction.objects.filter(customer_email__iexact=customer_email).order_by(
            "-created_at"
        )

    def list_by_customer_email(self, customer_email: str) -> QuerySet:
        """Return reward history filtered by customer email.

        Args:
            customer_email: Customer email used as the filter.

        Returns:
            QuerySet: Ordered reward transaction history.
        """
        return RewardTransaction.objects.filter(customer_email__iexact=customer_email).order_by(
            "-created_at"
        )

    def get_by_id_for_customer(self, transaction_id: UUID, customer):
        """Return a reward transaction by id scoped to a customer.

        Args:
            transaction_id: Reward transaction identifier.
            customer: Customer owner of the transaction.

        Returns:
            RewardTransaction | None: Matching transaction when found.
        """
        return RewardTransaction.objects.filter(id=transaction_id, customer=customer).first()

    def get_by_id(self, transaction_id: UUID):
        """Return a reward transaction by identifier.

        Args:
            transaction_id: Reward transaction identifier.

        Returns:
            RewardTransaction | None: Matching transaction when found.
        """
        return RewardTransaction.objects.filter(id=transaction_id).first()

    def apply_filters(
        self,
        queryset: QuerySet,
        *,
        type_filter: str | None = None,
        ordering: str | None = None,
    ) -> QuerySet:
        """Apply type and ordering filters to a reward transaction queryset.

        Args:
            queryset: Base queryset to filter.
            type_filter: Optional transaction type to filter by.
            ordering: Optional ordering field (prefix with ``-`` for descending).

        Returns:
            QuerySet: Filtered and ordered queryset.
        """
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset

    def none(self) -> QuerySet[RewardTransaction]:
        """Return an empty reward transaction queryset.

        Returns:
            QuerySet[RewardTransaction]: Empty queryset for schema and fallback flows.
        """
        return RewardTransaction.objects.none()
