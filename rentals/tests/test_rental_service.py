"""Tests for rental business logic."""

import uuid
from decimal import Decimal
from unittest.mock import call, patch

import pytest

from cars.models import Car
from core.exceptions import NotFoundError
from customers.models import Customer
from rentals.exceptions import CarNotAvailableError, RentalAlreadyReturnedError
from rentals.models import Rental
from rentals.services import RentalService


@pytest.fixture
def service() -> RentalService:
    return RentalService()


@pytest.mark.django_db
class TestCreateRental:
    def test_creates_rental_and_marks_car_unavailable(
        self, service: RentalService, economic_car: Car, customer: Customer
    ) -> None:
        rental = service.create_rental(
            car_id=economic_car.id,
            customer=customer,
            customer_name="John Doe",
            customer_email=customer.email,
            days=3,
        )
        assert rental.subtotal == Decimal("150.00")
        assert rental.duration_discount == Decimal("0")
        assert rental.reward_discount == Decimal("0.00")
        assert rental.total_cost == Decimal("150.00")
        economic_car.refresh_from_db()
        assert not economic_car.available

    def test_raises_not_found_for_missing_car(
        self, service: RentalService, customer: Customer
    ) -> None:
        with pytest.raises(NotFoundError):
            service.create_rental(
                car_id=uuid.uuid4(),
                customer=customer,
                customer_name="John",
                customer_email=customer.email,
                days=3,
            )

    def test_raises_car_not_available(
        self, service: RentalService, unavailable_car: Car, customer: Customer
    ) -> None:
        with pytest.raises(CarNotAvailableError):
            service.create_rental(
                car_id=unavailable_car.id,
                customer=customer,
                customer_name="John",
                customer_email=customer.email,
                days=3,
            )

    def test_no_discount_for_three_days(
        self, service: RentalService, economic_car: Car, customer: Customer
    ) -> None:
        rental = service.create_rental(
            car_id=economic_car.id,
            customer=customer,
            customer_name="John",
            customer_email=customer.email,
            days=3,
        )
        assert rental.total_cost == Decimal("150.00")  # 50 * 3, no discount

    def test_five_percent_discount_four_days(
        self, service: RentalService, economic_car: Car, customer: Customer
    ) -> None:
        rental = service.create_rental(
            car_id=economic_car.id,
            customer=customer,
            customer_name="John",
            customer_email=customer.email,
            days=4,
        )
        expected = Decimal("50.00") * 4 * Decimal("0.95")
        assert rental.total_cost == expected
        assert rental.duration_discount == Decimal("10.00")

    def test_ten_percent_discount_eight_days(
        self, service: RentalService, economic_car: Car, customer: Customer
    ) -> None:
        rental = service.create_rental(
            car_id=economic_car.id,
            customer=customer,
            customer_name="John",
            customer_email=customer.email,
            days=8,
        )
        expected = Decimal("50.00") * 8 * Decimal("0.90")
        assert rental.total_cost == expected
        assert rental.duration_discount == Decimal("40.00")

    def test_logs_started_and_completed(
        self, service: RentalService, economic_car: Car, customer: Customer
    ) -> None:
        with patch("rentals.services.logger") as logger_mock:
            rental = service.create_rental(
                car_id=economic_car.id,
                customer=customer,
                customer_name="John Doe",
                customer_email=customer.email,
                days=3,
            )

        logger_mock.info.assert_has_calls(
            [
                call(
                    "rental_create_started",
                    car_id=str(economic_car.id),
                    customer_email=customer.email,
                    days=3,
                ),
                call(
                    "rental_create_completed",
                    rental_id=str(rental.id),
                    car_id=str(economic_car.id),
                    customer_email=customer.email,
                    days=3,
                    total_cost="150.00",
                ),
            ],
            any_order=False,
        )


@pytest.mark.django_db
class TestReturnRental:
    def test_return_marks_car_available(
        self,
        service: RentalService,
        active_rental: Rental,
        economic_car: Car,
        customer: Customer,
    ) -> None:
        result = service.return_rental(active_rental.id, actor=customer)
        economic_car.refresh_from_db()
        assert economic_car.available
        assert result.rental.id == active_rental.id
        assert result.points_earned > 0
        assert result.reward_transaction_id is not None

    def test_raises_not_found(self, service: RentalService, customer: Customer) -> None:
        with pytest.raises(NotFoundError):
            service.return_rental(uuid.uuid4(), actor=customer)

    def test_raises_already_returned(
        self, service: RentalService, returned_rental: Rental, customer: Customer
    ) -> None:
        with pytest.raises(RentalAlreadyReturnedError):
            service.return_rental(returned_rental.id, actor=customer)

    def test_logs_started_and_completed(
        self,
        service: RentalService,
        active_rental: Rental,
        economic_car: Car,
        customer: Customer,
    ) -> None:
        with patch("rentals.services.logger") as logger_mock:
            result = service.return_rental(active_rental.id, actor=customer)

        logger_mock.info.assert_has_calls(
            [
                call(
                    "rental_return_started",
                    rental_id=str(active_rental.id),
                    actor_id=str(customer.pk),
                    actor_is_staff=False,
                ),
                call(
                    "rental_return_completed",
                    rental_id=str(active_rental.id),
                    car_id=str(economic_car.id),
                    returned_on_time=True,
                    late_fee="0",
                    points_earned=result.points_earned,
                ),
            ],
            any_order=False,
        )


class TestCalculateDiscount:
    def test_no_discount_for_short_rental(self) -> None:
        assert RentalService.calculate_discount(3, Decimal("150.00")) == Decimal("0")

    def test_five_percent_discount(self) -> None:
        result = RentalService.calculate_discount(4, Decimal("200.00"))
        assert result == Decimal("10.00")

    def test_ten_percent_discount(self) -> None:
        result = RentalService.calculate_discount(8, Decimal("400.00"))
        assert result == Decimal("40.00")

    def test_boundary_exactly_three_days_no_discount(self) -> None:
        assert RentalService.calculate_discount(3, Decimal("150.00")) == Decimal("0")

    def test_boundary_exactly_seven_days_five_percent(self) -> None:
        # 7 > 3 but not > 7, so 5%
        result = RentalService.calculate_discount(7, Decimal("350.00"))
        assert result == Decimal("17.50")


class TestCalculateLateFee:
    def test_late_fee_calculation(self) -> None:
        # 2 late days × $50/day × 2.0 multiplier = $200
        result = RentalService.calculate_late_fee(2, Decimal("50.00"))
        assert result == Decimal("200.00")

    def test_zero_late_days(self) -> None:
        result = RentalService.calculate_late_fee(0, Decimal("50.00"))
        assert result == Decimal("0")


@pytest.mark.django_db
class TestGetStats:
    def test_stats_with_rentals(
        self, service: RentalService, active_rental: Rental, economic_car: Car
    ) -> None:
        economic_car.available = False
        economic_car.save(update_fields=["available"])

        stats = service.get_stats()
        assert stats["total_rentals"] == 1
        assert stats["active_rentals"] == 1
        assert stats["available_cars"] == 0

    def test_stats_empty(self, service: RentalService) -> None:
        stats = service.get_stats()
        assert stats["total_rentals"] == 0
        assert stats["total_revenue"] == "0"
