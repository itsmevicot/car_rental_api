"""Business logic for the rentals domain."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from django.db import transaction as db_transaction
from django.utils import timezone

from cars.repositories import CarRepository
from core.exceptions import AuthorizationError, NotFoundError
from customers.repositories import CustomerRepository
from rentals.constants import (
    DISCOUNT_RATE_SHORT,
    DISCOUNT_RATE_WEEK,
    DISCOUNT_THRESHOLD_SHORT,
    DISCOUNT_THRESHOLD_WEEK,
    LATE_FEE_MULTIPLIER,
)
from rentals.dataclasses import RentalReturnResult
from rentals.exceptions import CarNotAvailableError, RentalAlreadyReturnedError
from rentals.repositories import RentalRepository

if TYPE_CHECKING:
    from uuid import UUID

    from rewards.services import RewardService

logger = structlog.get_logger(__name__)


class RentalService:
    """Orchestrates car-rental operations."""

    def __init__(
        self,
        rental_repo: RentalRepository | None = None,
        car_repo: CarRepository | None = None,
        customer_repo: CustomerRepository | None = None,
        reward_service: RewardService | None = None,
    ) -> None:
        self._rentals = rental_repo or RentalRepository()
        self._cars = car_repo or CarRepository()
        self._customers = customer_repo or CustomerRepository()
        self._reward_service = reward_service

    @property
    def reward_service(self) -> RewardService:
        if self._reward_service is None:
            from rewards.services import RewardService

            self._reward_service = RewardService()
        return self._reward_service

    @staticmethod
    def calculate_discount(days: int, total: Decimal) -> Decimal:
        if days > DISCOUNT_THRESHOLD_WEEK:
            return total * DISCOUNT_RATE_WEEK
        if days > DISCOUNT_THRESHOLD_SHORT:
            return total * DISCOUNT_RATE_SHORT
        return Decimal("0")

    @staticmethod
    def calculate_late_fee(late_days: int, daily_rate: Decimal) -> Decimal:
        return daily_rate * late_days * LATE_FEE_MULTIPLIER

    @staticmethod
    def display_name(customer, supplied_name: str | None = None) -> str:
        if supplied_name:
            return supplied_name
        full_name = customer.get_full_name()
        return full_name or customer.email

    def resolve_customer(self, email: str, name: str, *, is_staff: bool):
        customer = self._customers.get_by_email(email)
        if customer is not None:
            return customer
        if is_staff:
            return self._customers.create_user(email=email, password=None, first_name=name)
        return None

    def create_rental(
        self, car_id: UUID, customer, customer_name: str, customer_email: str, days: int
    ):
        logger.info(
            "rental_create_started",
            car_id=str(car_id),
            customer_email=customer_email,
            days=days,
        )

        try:
            with db_transaction.atomic():
                car = self._cars.get_by_id_for_update(car_id)
                if car is None:
                    raise NotFoundError("Car", car_id)
                if not car.available:
                    raise CarNotAvailableError()

                subtotal = car.daily_rate * days
                duration_discount = self.calculate_discount(days, subtotal)
                total_cost = subtotal - duration_discount

                start_date = timezone.now()
                end_date = start_date + timedelta(days=days)
                rental = self._rentals.create(
                    car=car,
                    customer=customer,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    start_date=start_date,
                    end_date=end_date,
                    subtotal=subtotal,
                    duration_discount=duration_discount,
                    reward_discount=Decimal("0.00"),
                    total_cost=total_cost,
                )
                self._cars.update_availability(car, available=False)
        except Exception as exc:
            logger.warning(
                "rental_create_failed",
                car_id=str(car_id),
                customer_email=customer_email,
                days=days,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise

        logger.info(
            "rental_create_completed",
            rental_id=str(rental.id),
            car_id=str(car.id),
            customer_email=customer_email,
            days=days,
            total_cost=f"{total_cost:.2f}",
        )
        return rental

    def return_rental(self, rental_id: UUID, actor):
        logger.info(
            "rental_return_started",
            rental_id=str(rental_id),
            actor_id=str(actor.pk),
            actor_is_staff=actor.is_staff,
        )

        try:
            with db_transaction.atomic():
                rental = self._rentals.get_by_id_for_update(rental_id)
                if rental is None:
                    raise NotFoundError("Rental", rental_id)
                if not actor.is_staff and rental.customer_id != actor.pk:
                    raise AuthorizationError()
                if rental.returned:
                    raise RentalAlreadyReturnedError()

                rental.ensure_pricing_breakdown()
                rental.returned = True
                rental.actual_return_date = timezone.now()
                returned_on_time = rental.actual_return_date <= rental.end_date

                if not returned_on_time:
                    late_days = (rental.actual_return_date - rental.end_date).days
                    if late_days > 0:
                        rental.late_fee = self.calculate_late_fee(late_days, rental.car.daily_rate)
                        rental.total_cost = rental.calculate_total_cost()

                self._rentals.save_return(rental)
                self._cars.update_availability(rental.car, available=True)
                transaction = self.reward_service.award_points(rental, returned_on_time)
        except Exception as exc:
            logger.warning(
                "rental_return_failed",
                rental_id=str(rental_id),
                actor_id=str(actor.pk),
                actor_is_staff=actor.is_staff,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise

        logger.info(
            "rental_return_completed",
            rental_id=str(rental.id),
            car_id=str(rental.car.id),
            returned_on_time=returned_on_time,
            late_fee=str(rental.late_fee or 0),
            points_earned=transaction.points,
        )
        return RentalReturnResult(
            rental=rental,
            points_earned=transaction.points,
            reward_transaction_id=transaction.id,
        )

    def get_visible_rental(self, rental_id: UUID, actor):
        rental = self._rentals.get_by_id(rental_id)
        if rental is None:
            raise NotFoundError("Rental", rental_id)
        if not actor.is_staff and rental.customer_id != actor.pk:
            raise NotFoundError("Rental", rental_id)
        return rental

    def list_all(self):
        return self._rentals.list_all()

    def empty_list(self):
        return self._rentals.none()

    def list_by_customer(self, customer):
        return self._rentals.list_by_customer(customer)

    def list_by_customer_email(self, customer_email: str):
        return self._rentals.list_by_customer_email(customer_email)

    def list_by_customer_id(self, customer_id):
        customer = self._customers.get_by_id(customer_id)
        if customer is None:
            raise NotFoundError("Customer", customer_id)
        return self._rentals.list_by_customer_id(customer_id)

    def get_stats(self) -> dict:
        rental_stats = self._rentals.aggregate_stats()
        car_stats = self._cars.aggregate_counts()
        return {
            "total_rentals": rental_stats["total_rentals"],
            "active_rentals": rental_stats["active_rentals"],
            "total_revenue": str(rental_stats["total_revenue"] or Decimal("0")),
            "total_cars": car_stats["total_cars"],
            "available_cars": car_stats["available_cars"],
        }
