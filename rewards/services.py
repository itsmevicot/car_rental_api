"""Business logic for the customer rewards program."""

import math
from decimal import Decimal
from uuid import UUID

import structlog
from django.db import transaction as db_transaction
from django.db.models import QuerySet

from cars.models import CarCategory
from core.exceptions import NotFoundError
from customers.models import Customer
from customers.repositories import CustomerRepository
from rentals.models import Rental
from rentals.repositories import RentalRepository
from rewards.constants import (
    BASE_POINTS_PER_DAY,
    BRONZE_MULTIPLIER,
    DISCOUNT_VALUE,
    EXTENDED_BONUS_DAYS,
    EXTENDED_BONUS_POINTS,
    GOLD_MULTIPLIER,
    GOLD_THRESHOLD,
    MIN_REDEEM_POINTS,
    ON_TIME_BONUS,
    POINTS_PER_DISCOUNT,
    PREMIUM_BONUS_PER_DAY,
    SILVER_MULTIPLIER,
    SILVER_THRESHOLD,
    STANDARD_BONUS_PER_DAY,
    WEEK_BONUS_DAYS,
    WEEK_BONUS_POINTS,
)
from rewards.exceptions import (
    CustomerMismatchError,
    InsufficientPointsError,
    MinimumRedemptionError,
)
from rewards.models import CustomerTier, RewardTransaction, TransactionType
from rewards.repositories import RewardRepository

logger = structlog.get_logger(__name__)


class RewardService:
    """Manages the customer loyalty rewards program."""

    def __init__(
        self,
        repository: RewardRepository | None = None,
        customer_repo: CustomerRepository | None = None,
        rental_repo: RentalRepository | None = None,
    ) -> None:
        self._repo = repository or RewardRepository()
        self._customers = customer_repo or CustomerRepository()
        self._rentals = rental_repo or RentalRepository()

    @staticmethod
    def _tier_from_lifetime(lifetime_earned: int) -> tuple[str, Decimal]:
        """Return the loyalty tier for a lifetime earned amount.

        Args:
            lifetime_earned: Total earned points over the customer lifetime.

        Returns:
            tuple[str, Decimal]: Tier name and multiplier.
        """
        if lifetime_earned >= GOLD_THRESHOLD:
            return CustomerTier.GOLD, GOLD_MULTIPLIER
        if lifetime_earned >= SILVER_THRESHOLD:
            return CustomerTier.SILVER, SILVER_MULTIPLIER
        return CustomerTier.BRONZE, BRONZE_MULTIPLIER

    def get_customer_tier(self, customer_email: str) -> tuple[str, Decimal]:
        """Return the loyalty tier for a customer email.

        Args:
            customer_email: Customer email used to calculate lifetime points.

        Returns:
            tuple[str, Decimal]: Tier name and multiplier.
        """
        return self._tier_from_lifetime(self._repo.get_lifetime_earned(customer_email))

    def get_customer_tier_for_customer(self, customer: Customer) -> tuple[str, Decimal]:
        """Return the loyalty tier for a customer instance.

        Args:
            customer: Customer whose tier should be calculated.

        Returns:
            tuple[str, Decimal]: Tier name and multiplier.
        """
        return self._tier_from_lifetime(self._repo.get_lifetime_earned_for_customer(customer))

    @staticmethod
    def calculate_points(rental: Rental, returned_on_time: bool) -> int:
        """Calculate raw reward points for a rental.

        Args:
            rental: Rental being scored.
            returned_on_time: Whether the rental was returned on time.

        Returns:
            int: Raw points before tier multiplier application.
        """
        days = (rental.end_date - rental.start_date).days
        points = BASE_POINTS_PER_DAY * days

        category = rental.car.category
        if category == CarCategory.PREMIUM:
            points += PREMIUM_BONUS_PER_DAY * days
        elif category == CarCategory.STANDARD:
            points += STANDARD_BONUS_PER_DAY * days

        if days >= EXTENDED_BONUS_DAYS:
            points += EXTENDED_BONUS_POINTS
        elif days >= WEEK_BONUS_DAYS:
            points += WEEK_BONUS_POINTS
        if returned_on_time:
            points += ON_TIME_BONUS
        return points

    @staticmethod
    def _earned_breakdown(
        rental: Rental,
        returned_on_time: bool,
        *,
        base_points: int,
        category_bonus_points: int,
        duration_bonus_points: int,
        on_time_bonus_points: int,
        tier: str,
        multiplier: Decimal,
    ) -> dict[str, str | int | bool]:
        """Build the persisted points-earned breakdown payload.

        Args:
            rental: Rental being scored.
            returned_on_time: Whether the rental was returned on time.
            base_points: Base points from rental duration.
            category_bonus_points: Category bonus points.
            duration_bonus_points: Duration bonus points.
            on_time_bonus_points: On-time return bonus points.
            tier: Tier name applied to the calculation.
            multiplier: Tier multiplier applied to the subtotal.

        Returns:
            dict[str, str | int | bool]: Breakdown payload stored on the transaction.
        """
        return {
            "rental_days": (rental.end_date - rental.start_date).days,
            "category": rental.car.category,
            "returned_on_time": returned_on_time,
            "base_points": base_points,
            "category_bonus_points": category_bonus_points,
            "duration_bonus_points": duration_bonus_points,
            "on_time_bonus_points": on_time_bonus_points,
            "tier_applied": tier,
            "tier_multiplier": str(multiplier),
        }

    @staticmethod
    def _redeemed_breakdown(
        *,
        requested_points: int,
        discount_units: int,
        discount_amount: Decimal,
        available_points_before: int,
        available_points_after: int,
    ) -> dict[str, str | int]:
        """Build the persisted points-redeemed breakdown payload.

        Args:
            requested_points: Points requested by the caller.
            discount_units: Number of discount units actually redeemed.
            discount_amount: Monetary discount applied.
            available_points_before: Balance before redemption.
            available_points_after: Balance after redemption.

        Returns:
            dict[str, str | int]: Breakdown payload stored on the transaction.
        """
        return {
            "requested_points": requested_points,
            "discount_units": discount_units,
            "discount_amount": str(discount_amount),
            "available_points_before": available_points_before,
            "available_points_after": available_points_after,
        }

    def award_points(self, rental: Rental, returned_on_time: bool) -> RewardTransaction:
        """Award loyalty points for a returned rental.

        Args:
            rental: Returned rental.
            returned_on_time: Whether the rental was returned on time.

        Returns:
            RewardTransaction: Created earned-points transaction.

        Raises:
            NotFoundError: If the customer tied to the rental cannot be locked.
        """
        logger.info(
            "reward_award_started",
            rental_id=str(rental.id),
            customer_email=rental.customer.email,
            returned_on_time=returned_on_time,
        )

        try:
            with db_transaction.atomic():
                locked_customer = self._customers.get_by_id_for_update(rental.customer_id)
                if locked_customer is None:
                    raise NotFoundError("Customer", rental.customer_id)
                days = (rental.end_date - rental.start_date).days
                base_points = BASE_POINTS_PER_DAY * days

                category_bonus_points = 0
                if rental.car.category == CarCategory.PREMIUM:
                    category_bonus_points = PREMIUM_BONUS_PER_DAY * days
                elif rental.car.category == CarCategory.STANDARD:
                    category_bonus_points = STANDARD_BONUS_PER_DAY * days

                duration_bonus_points = 0
                if days >= EXTENDED_BONUS_DAYS:
                    duration_bonus_points = EXTENDED_BONUS_POINTS
                elif days >= WEEK_BONUS_DAYS:
                    duration_bonus_points = WEEK_BONUS_POINTS

                on_time_bonus_points = ON_TIME_BONUS if returned_on_time else 0
                subtotal_points = (
                    base_points
                    + category_bonus_points
                    + duration_bonus_points
                    + on_time_bonus_points
                )

                tier, multiplier = self.get_customer_tier_for_customer(rental.customer)
                final_points = math.floor(subtotal_points * multiplier)
                on_time_label = "on-time return" if returned_on_time else "late return"

                transaction = self._repo.create(
                    customer=rental.customer,
                    customer_email=rental.customer.email,
                    rental=rental,
                    type=TransactionType.EARNED,
                    points=final_points,
                    reason=f"Rental {rental.id} - {days}-day rental with {on_time_label}",
                    breakdown=self._earned_breakdown(
                        rental,
                        returned_on_time,
                        base_points=base_points,
                        category_bonus_points=category_bonus_points,
                        duration_bonus_points=duration_bonus_points,
                        on_time_bonus_points=on_time_bonus_points,
                        tier=tier,
                        multiplier=multiplier,
                    ),
                    idempotency_key=f"earned:{rental.id}",
                )
        except Exception as exc:
            logger.warning(
                "reward_award_failed",
                rental_id=str(rental.id),
                customer_email=rental.customer.email,
                returned_on_time=returned_on_time,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise

        logger.info(
            "reward_award_completed",
            customer_email=rental.customer.email,
            rental_id=str(rental.id),
            base_points=base_points,
            multiplier=str(multiplier),
            final_points=final_points,
        )

        logger.info(
            "points_awarded",
            customer_email=rental.customer.email,
            rental_id=str(rental.id),
            base_points=base_points,
            multiplier=str(multiplier),
            final_points=final_points,
        )
        return transaction

    def get_customer_summary(self, customer: Customer) -> dict[str, str | int]:
        """Return reward summary data for a customer.

        Args:
            customer: Customer whose reward summary should be returned.

        Returns:
            dict[str, str | int]: Reward summary payload.
        """
        lifetime_earned = self._repo.get_lifetime_earned_for_customer(customer)
        lifetime_redeemed = self._repo.get_lifetime_redeemed_for_customer(customer)
        total_points = lifetime_earned - lifetime_redeemed
        tier, _ = self._tier_from_lifetime(lifetime_earned)

        if tier == CustomerTier.GOLD:
            points_to_next = 0
        elif tier == CustomerTier.SILVER:
            points_to_next = GOLD_THRESHOLD - lifetime_earned
        else:
            points_to_next = SILVER_THRESHOLD - lifetime_earned

        return {
            "customer_email": customer.email,
            "total_points": total_points,
            "tier": tier,
            "points_to_next_tier": max(0, points_to_next),
            "lifetime_points_earned": lifetime_earned,
            "lifetime_points_redeemed": lifetime_redeemed,
        }

    def get_customer_summary_by_email(self, customer_email: str) -> dict[str, str | int]:
        """Return reward summary data for a customer email.

        Args:
            customer_email: Customer email filter.

        Returns:
            dict[str, str | int]: Reward summary payload.
        """
        lifetime_earned = self._repo.get_lifetime_earned(customer_email)
        lifetime_redeemed = self._repo.get_lifetime_redeemed(customer_email)
        total_points = lifetime_earned - lifetime_redeemed
        tier, _ = self.get_customer_tier(customer_email)

        if tier == CustomerTier.GOLD:
            points_to_next = 0
        elif tier == CustomerTier.SILVER:
            points_to_next = GOLD_THRESHOLD - lifetime_earned
        else:
            points_to_next = SILVER_THRESHOLD - lifetime_earned

        return {
            "customer_email": customer_email,
            "total_points": total_points,
            "tier": tier,
            "points_to_next_tier": max(0, points_to_next),
            "lifetime_points_earned": lifetime_earned,
            "lifetime_points_redeemed": lifetime_redeemed,
        }

    def get_customer_history(self, customer: Customer) -> QuerySet[RewardTransaction]:
        """Return reward history for a customer.

        Args:
            customer: Customer whose history should be returned.

        Returns:
            QuerySet[RewardTransaction]: Ordered reward transactions.
        """
        return self._repo.list_by_customer(customer)

    def filter_history(
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
            ordering: Optional ordering field.

        Returns:
            QuerySet: Filtered and ordered queryset.
        """
        return self._repo.apply_filters(queryset, type_filter=type_filter, ordering=ordering)

    def get_customer_history_by_email(self, customer_email: str) -> QuerySet[RewardTransaction]:
        """Return reward history for a customer email.

        Args:
            customer_email: Customer email filter.

        Returns:
            QuerySet[RewardTransaction]: Ordered reward transactions.
        """
        return self._repo.list_by_customer_email(customer_email)

    def empty_history(self) -> QuerySet[RewardTransaction]:
        """Return an empty reward history queryset.

        Returns:
            QuerySet[RewardTransaction]: Empty queryset used by schema generation flows.
        """
        return self._repo.none()

    def get_customer_summary_by_id(self, customer_id: UUID) -> dict[str, str | int]:
        """Return reward summary data for a customer identifier.

        Args:
            customer_id: Customer identifier.

        Returns:
            dict[str, str | int]: Reward summary payload.

        Raises:
            NotFoundError: If the customer does not exist.
        """
        customer = self._customers.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)
        return self.get_customer_summary(customer)

    def get_customer_history_by_id(self, customer_id: UUID) -> QuerySet[RewardTransaction]:
        """Return reward history for a customer identifier.

        Args:
            customer_id: Customer identifier.

        Returns:
            QuerySet[RewardTransaction]: Ordered reward transactions.

        Raises:
            NotFoundError: If the customer does not exist.
        """
        customer = self._customers.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)
        return self.get_customer_history(customer)

    def resolve_customer_by_email(self, customer_email: str) -> Customer:
        """Resolve a customer by email.

        Args:
            customer_email: Customer email to resolve.

        Returns:
            Customer: Matching customer instance.

        Raises:
            NotFoundError: If the customer does not exist.
        """
        customer = self._customers.get_by_email(customer_email)
        if customer is None:
            raise NotFoundError("Customer", customer_email)
        return customer

    def resolve_customer_by_id(self, customer_id: UUID) -> Customer:
        """Resolve a customer by identifier.

        Args:
            customer_id: Customer identifier to resolve.

        Returns:
            Customer: Matching customer instance.

        Raises:
            NotFoundError: If the customer does not exist.
        """
        customer = self._customers.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)
        return customer

    def get_transaction_detail(self, transaction_id: UUID, actor: Customer) -> RewardTransaction:
        """Return a reward transaction visible to the actor.

        Args:
            transaction_id: Target reward transaction identifier.
            actor: Authenticated actor requesting the transaction.

        Returns:
            RewardTransaction: Matching transaction.

        Raises:
            NotFoundError: If the transaction is not visible or does not exist.
        """
        if actor.is_staff:
            transaction = self._repo.get_by_id(transaction_id)
        else:
            transaction = self._repo.get_by_id_for_customer(transaction_id, actor)
        if transaction is None:
            raise NotFoundError("Reward transaction", transaction_id)
        return transaction

    def redeem_points(
        self,
        rental_id: UUID,
        customer: Customer,
        points_to_redeem: int,
    ) -> RewardTransaction:
        """Redeem customer points against a rental.

        Args:
            rental_id: Target rental identifier.
            customer: Customer redeeming the points.
            points_to_redeem: Requested points to redeem.

        Returns:
            RewardTransaction: Created redeemed-points transaction.

        Raises:
            MinimumRedemptionError: If the request is below the minimum threshold.
            NotFoundError: If the customer or rental does not exist.
            CustomerMismatchError: If the rental belongs to another customer.
            InsufficientPointsError: If the balance is too low.
        """
        logger.info(
            "reward_redeem_started",
            rental_id=str(rental_id),
            customer_email=customer.email,
            requested_points=points_to_redeem,
        )

        if points_to_redeem < MIN_REDEEM_POINTS:
            exc = MinimumRedemptionError()
            logger.warning(
                "reward_redeem_failed",
                rental_id=str(rental_id),
                customer_email=customer.email,
                requested_points=points_to_redeem,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise exc

        try:
            with db_transaction.atomic():
                locked_customer = self._customers.get_by_id_for_update(customer.pk)
                if locked_customer is None:
                    raise NotFoundError("Customer", customer.pk)
                rental = self._rentals.get_by_id_for_update(rental_id)
                if rental is None:
                    raise NotFoundError("Rental", rental_id)

                if rental.customer_id != customer.pk:
                    raise CustomerMismatchError()

                available_before = self._repo.get_balance_for_customer(customer)
                if points_to_redeem > available_before:
                    raise InsufficientPointsError(available_before, points_to_redeem)

                discount_units = points_to_redeem // POINTS_PER_DISCOUNT
                actual_points = discount_units * POINTS_PER_DISCOUNT
                discount_amount = discount_units * DISCOUNT_VALUE
                available_after = available_before - actual_points

                rental.ensure_pricing_breakdown()
                rental.reward_discount += discount_amount
                rental.total_cost = rental.calculate_total_cost()
                rental.save(
                    update_fields=[
                        "subtotal",
                        "reward_discount",
                        "total_cost",
                        "updated_at",
                    ]
                )

                transaction = self._repo.create(
                    customer=customer,
                    customer_email=customer.email,
                    rental=rental,
                    type=TransactionType.REDEEMED,
                    points=-actual_points,
                    reason=f"Discount on rental {rental.id}",
                    breakdown=self._redeemed_breakdown(
                        requested_points=points_to_redeem,
                        discount_units=discount_units,
                        discount_amount=discount_amount,
                        available_points_before=available_before,
                        available_points_after=available_after,
                    ),
                    idempotency_key=None,
                )
        except Exception as exc:
            logger.warning(
                "reward_redeem_failed",
                rental_id=str(rental_id),
                customer_email=customer.email,
                requested_points=points_to_redeem,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise

        logger.info(
            "reward_redeem_completed",
            customer_email=customer.email,
            rental_id=str(rental.id),
            points_redeemed=actual_points,
            discount_amount=str(discount_amount),
            available_points_after=available_after,
        )

        logger.info(
            "points_redeemed",
            customer_email=customer.email,
            rental_id=str(rental_id),
            points_redeemed=actual_points,
            discount_amount=f"{discount_amount:.2f}",
        )
        return transaction
