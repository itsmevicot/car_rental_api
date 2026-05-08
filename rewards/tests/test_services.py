"""Tests for reward business logic."""

import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import call, patch

import pytest
from django.utils import timezone

from cars.models import Car
from core.exceptions import NotFoundError
from customers.models import Customer
from rentals.models import Rental
from rewards.exceptions import (
    CustomerMismatchError,
    InsufficientPointsError,
    MinimumRedemptionError,
)
from rewards.models import RewardTransaction, TransactionType
from rewards.services import RewardService


@pytest.fixture
def service() -> RewardService:
    return RewardService()


def _make_rental(car: Car, customer: Customer, days: int) -> Rental:
    now = timezone.now()
    return Rental.objects.create(
        car=car,
        customer=customer,
        customer_name=customer.get_full_name() or customer.email,
        customer_email=customer.email,
        start_date=now,
        end_date=now + timedelta(days=days),
        total_cost=car.daily_rate * days,
    )


def _earn(customer: Customer, rental: Rental, points: int) -> RewardTransaction:
    return RewardTransaction.objects.create(
        customer=customer,
        customer_email=customer.email,
        rental=rental,
        type=TransactionType.EARNED,
        points=points,
        reason="test seed",
    )


@pytest.mark.django_db
class TestCalculatePoints:
    def test_economic_car_3_days_on_time(self, economic_car: Car, customer: Customer) -> None:
        rental = _make_rental(economic_car, customer, days=3)
        points = RewardService.calculate_points(rental, returned_on_time=True)
        assert points == 10 * 3 + 25  # 55

    def test_standard_car_5_days_on_time(self, standard_car: Car, customer: Customer) -> None:
        rental = _make_rental(standard_car, customer, days=5)
        points = RewardService.calculate_points(rental, returned_on_time=True)
        assert points == (10 + 5) * 5 + 25  # 100

    def test_premium_car_8_days_on_time(self, premium_car: Car, customer: Customer) -> None:
        rental = _make_rental(premium_car, customer, days=8)
        points = RewardService.calculate_points(rental, returned_on_time=True)
        assert points == (10 + 10) * 8 + 50 + 25  # 235

    def test_premium_car_14_days_late(self, premium_car: Car, customer: Customer) -> None:
        rental = _make_rental(premium_car, customer, days=14)
        points = RewardService.calculate_points(rental, returned_on_time=False)
        assert points == (10 + 10) * 14 + 150  # 430

    def test_economic_car_7_days_on_time_week_bonus(
        self, economic_car: Car, customer: Customer
    ) -> None:
        rental = _make_rental(economic_car, customer, days=7)
        points = RewardService.calculate_points(rental, returned_on_time=True)
        assert points == 10 * 7 + 50 + 25  # 145

    def test_no_on_time_bonus_when_late(self, economic_car: Car, customer: Customer) -> None:
        rental = _make_rental(economic_car, customer, days=3)
        points = RewardService.calculate_points(rental, returned_on_time=False)
        assert points == 10 * 3  # 30


@pytest.mark.django_db
class TestGetCustomerTier:
    def test_bronze_tier_zero_points(self, service: RewardService, customer: Customer) -> None:
        tier, multiplier = service.get_customer_tier(customer.email)
        assert tier == "Bronze"
        assert multiplier == Decimal("1.0")

    def test_bronze_tier_499_points(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=1)
        _earn(customer, rental, 499)
        tier, _ = service.get_customer_tier(customer.email)
        assert tier == "Bronze"

    def test_silver_tier_500_points(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=1)
        _earn(customer, rental, 500)
        tier, multiplier = service.get_customer_tier(customer.email)
        assert tier == "Silver"
        assert multiplier == Decimal("1.25")

    def test_silver_tier_999_points(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=1)
        _earn(customer, rental, 999)
        tier, _ = service.get_customer_tier(customer.email)
        assert tier == "Silver"

    def test_gold_tier_1000_points(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=1)
        _earn(customer, rental, 1000)
        tier, multiplier = service.get_customer_tier(customer.email)
        assert tier == "Gold"
        assert multiplier == Decimal("1.5")


@pytest.mark.django_db
class TestAwardPoints:
    def test_awards_points_on_return(
        self, service: RewardService, economic_car: Car, customer: Customer
    ) -> None:
        now = timezone.now()
        rental = Rental.objects.create(
            car=economic_car,
            customer=customer,
            customer_name="John Doe",
            customer_email=customer.email,
            start_date=now,
            end_date=now + timedelta(days=3),
            total_cost=Decimal("150.00"),
            returned=True,
            actual_return_date=now + timedelta(days=2),
        )
        transaction = service.award_points(rental, returned_on_time=True)
        assert transaction.type == TransactionType.EARNED
        assert transaction.points == 55  # 10*3 + 25
        assert transaction.customer_email == customer.email
        assert transaction.breakdown == {
            "rental_days": 3,
            "category": "economic",
            "returned_on_time": True,
            "base_points": 30,
            "category_bonus_points": 0,
            "duration_bonus_points": 0,
            "on_time_bonus_points": 25,
            "tier_applied": "Bronze",
            "tier_multiplier": "1.0",
        }

    def test_applies_silver_tier_multiplier(
        self, service: RewardService, economic_car: Car, customer: Customer
    ) -> None:
        # Seed Silver tier (600 earned points)
        seed_rental = _make_rental(economic_car, customer, days=1)
        _earn(customer, seed_rental, 600)

        now = timezone.now()
        rental = Rental.objects.create(
            car=economic_car,
            customer=customer,
            customer_name="John Doe",
            customer_email=customer.email,
            start_date=now,
            end_date=now + timedelta(days=3),
            total_cost=Decimal("150.00"),
            returned=True,
            actual_return_date=now + timedelta(days=2),
        )
        transaction = service.award_points(rental, returned_on_time=True)
        # Base: 55 pts, Silver 1.25x → floor(68.75) = 68
        assert transaction.points == 68
        assert transaction.breakdown["tier_applied"] == "Silver"
        assert transaction.breakdown["tier_multiplier"] == "1.25"

    def test_idempotency_key_prevents_duplicate(
        self, service: RewardService, economic_car: Car, customer: Customer
    ) -> None:
        """Second award on same rental must not create a duplicate transaction."""
        now = timezone.now()
        rental = Rental.objects.create(
            car=economic_car,
            customer=customer,
            customer_name="John Doe",
            customer_email=customer.email,
            start_date=now,
            end_date=now + timedelta(days=3),
            total_cost=Decimal("150.00"),
            returned=True,
            actual_return_date=now + timedelta(days=2),
        )
        service.award_points(rental, returned_on_time=True)
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            service.award_points(rental, returned_on_time=True)

    def test_logs_started_and_completed(
        self, service: RewardService, economic_car: Car, customer: Customer
    ) -> None:
        now = timezone.now()
        rental = Rental.objects.create(
            car=economic_car,
            customer=customer,
            customer_name="John Doe",
            customer_email=customer.email,
            start_date=now,
            end_date=now + timedelta(days=3),
            total_cost=Decimal("150.00"),
            returned=True,
            actual_return_date=now + timedelta(days=2),
        )

        with patch("rewards.services.logger") as logger_mock:
            transaction = service.award_points(rental, returned_on_time=True)

        logger_mock.info.assert_has_calls(
            [
                call(
                    "reward_award_started",
                    rental_id=str(rental.id),
                    customer_email=customer.email,
                    returned_on_time=True,
                ),
                call(
                    "reward_award_completed",
                    customer_email=customer.email,
                    rental_id=str(rental.id),
                    base_points=30,
                    multiplier="1.0",
                    final_points=55,
                ),
            ],
            any_order=False,
        )
        assert transaction.points == 55


@pytest.mark.django_db
class TestGetCustomerSummary:
    def test_summary_with_no_history(self, service: RewardService, customer: Customer) -> None:
        summary = service.get_customer_summary(customer)
        assert summary["total_points"] == 0
        assert summary["tier"] == "Bronze"
        assert summary["points_to_next_tier"] == 500
        assert summary["lifetime_points_earned"] == 0
        assert summary["lifetime_points_redeemed"] == 0

    def test_summary_with_transactions(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=3)
        _earn(customer, rental, 200)
        RewardTransaction.objects.create(
            customer=customer,
            customer_email=customer.email,
            rental=rental,
            type=TransactionType.REDEEMED,
            points=-100,
            reason="redeemed",
        )
        summary = service.get_customer_summary(customer)
        assert summary["total_points"] == 100
        assert summary["lifetime_points_earned"] == 200
        assert summary["lifetime_points_redeemed"] == 100

    def test_summary_by_email_not_found(self, service: RewardService) -> None:
        summary = service.get_customer_summary_by_email("nobody@example.com")
        assert summary["total_points"] == 0
        assert summary["tier"] == "Bronze"


@pytest.mark.django_db
class TestRedeemPoints:
    def test_redeem_success(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=10)
        _earn(customer, rental, 300)

        transaction = service.redeem_points(rental.id, customer, 200)
        assert transaction.points == -200
        assert transaction.type == TransactionType.REDEEMED
        assert transaction.breakdown == {
            "requested_points": 200,
            "discount_units": 2,
            "discount_amount": "100.00",
            "available_points_before": 300,
            "available_points_after": 100,
        }

        rental.refresh_from_db()
        assert rental.reward_discount == Decimal("100.00")
        assert rental.total_cost == Decimal("400.00")  # 500 - 100 (2 × $50)

    def test_redeem_insufficient_points(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=3)
        _earn(customer, rental, 50)
        with pytest.raises(InsufficientPointsError):
            service.redeem_points(rental.id, customer, 200)

    def test_redeem_below_minimum(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=3)
        _earn(customer, rental, 300)
        with pytest.raises(MinimumRedemptionError):
            service.redeem_points(rental.id, customer, 50)

    def test_redeem_nonexistent_rental(self, service: RewardService, customer: Customer) -> None:
        with pytest.raises(NotFoundError):
            service.redeem_points(uuid.uuid4(), customer, 100)

    def test_redeem_customer_mismatch(
        self, service: RewardService, customer: Customer, staff_user: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, staff_user, days=3)
        _earn(customer, rental, 300)
        with pytest.raises(CustomerMismatchError):
            service.redeem_points(rental.id, customer, 100)

    def test_redeem_rounds_down_to_discount_units(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=10)
        _earn(customer, rental, 500)

        transaction = service.redeem_points(rental.id, customer, 250)
        # 250 // 100 = 2 units → 200 actual points deducted
        assert transaction.points == -200

    def test_redeem_does_not_go_below_zero_cost(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        now = timezone.now()
        rental = Rental.objects.create(
            car=economic_car,
            customer=customer,
            customer_name="John Doe",
            customer_email=customer.email,
            start_date=now,
            end_date=now + timedelta(days=1),
            total_cost=Decimal("30.00"),
        )
        _earn(customer, rental, 500)

        service.redeem_points(rental.id, customer, 200)
        rental.refresh_from_db()
        assert rental.reward_discount == Decimal("100.00")
        assert rental.total_cost == Decimal("0")

    def test_logs_started_and_completed_for_redeem(
        self, service: RewardService, customer: Customer, economic_car: Car
    ) -> None:
        rental = _make_rental(economic_car, customer, days=10)
        _earn(customer, rental, 300)

        with patch("rewards.services.logger") as logger_mock:
            transaction = service.redeem_points(rental.id, customer, 200)

        logger_mock.info.assert_has_calls(
            [
                call(
                    "reward_redeem_started",
                    rental_id=str(rental.id),
                    customer_email=customer.email,
                    requested_points=200,
                ),
                call(
                    "reward_redeem_completed",
                    customer_email=customer.email,
                    rental_id=str(rental.id),
                    points_redeemed=200,
                    discount_amount="100.00",
                    available_points_after=100,
                ),
            ],
            any_order=False,
        )
        assert transaction.points == -200
