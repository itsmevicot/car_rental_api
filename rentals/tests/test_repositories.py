"""Tests for rental repository helpers."""

from rentals.repositories import RentalRepository


def test_rental_repository_queries(active_rental) -> None:
    repo = RentalRepository()
    assert repo.get_by_id(active_rental.id) == active_rental
    assert list(repo.list_by_customer(active_rental.customer)) == [active_rental]
    assert list(repo.list_by_customer_id(active_rental.customer_id)) == [active_rental]
    assert repo.none().count() == 0
