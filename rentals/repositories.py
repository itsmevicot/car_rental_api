"""Data-access layer for the rentals domain."""

from uuid import UUID

from django.db.models import Count, Q, QuerySet, Sum

from rentals.models import Rental


class RentalRepository:
    """Persist and fetch rentals."""

    def create(self, **kwargs) -> Rental:
        """Create and return a rental.

        Args:
            **kwargs: Rental fields to persist.

        Returns:
            Rental: Newly created rental instance.
        """
        return Rental.objects.create(**kwargs)

    def get_by_id_for_update(self, rental_id: UUID) -> Rental | None:
        """Lock and return a rental by identifier.

        Args:
            rental_id: Target rental identifier.

        Returns:
            Rental | None: Matching locked rental when found, otherwise ``None``.
        """
        return Rental.objects.select_for_update().filter(id=rental_id).first()

    def get_by_id(self, rental_id: UUID) -> Rental | None:
        """Return a rental by identifier.

        Args:
            rental_id: Target rental identifier.

        Returns:
            Rental | None: Matching rental with related car and customer when found.
        """
        return Rental.objects.select_related("car", "customer").filter(id=rental_id).first()

    def save_return(self, rental: Rental) -> None:
        """Persist a rental return mutation.

        Args:
            rental: Rental instance updated during the return flow.
        """
        rental.save(
            update_fields=[
                "returned",
                "actual_return_date",
                "late_fee",
                "total_cost",
                "updated_at",
            ]
        )

    def list_all(self) -> QuerySet[Rental]:
        """Return all rentals with relations loaded.

        Returns:
            QuerySet[Rental]: Rental queryset with car and customer eagerly loaded.
        """
        return Rental.objects.select_related("car", "customer").all()

    def list_by_customer(self, customer) -> QuerySet[Rental]:
        """Return rentals for a specific customer.

        Args:
            customer: Customer owner of the rentals.

        Returns:
            QuerySet[Rental]: Rentals belonging to the given customer.
        """
        return Rental.objects.select_related("car").filter(customer=customer)

    def list_by_customer_email(self, email: str) -> QuerySet[Rental]:
        """Return rentals filtered by customer email.

        Args:
            email: Customer email filter.

        Returns:
            QuerySet[Rental]: Rentals owned by the given email.
        """
        return Rental.objects.select_related("car").filter(customer_email__iexact=email)

    def list_by_customer_id(self, customer_id: UUID) -> QuerySet[Rental]:
        """Return rentals filtered by customer identifier.

        Args:
            customer_id: Customer identifier filter.

        Returns:
            QuerySet[Rental]: Rentals owned by the given customer id.
        """
        return Rental.objects.select_related("car").filter(customer_id=customer_id)

    def none(self) -> QuerySet[Rental]:
        """Return an empty rental queryset.

        Returns:
            QuerySet[Rental]: Empty queryset for schema and fallback flows.
        """
        return Rental.objects.none()

    def aggregate_stats(self) -> dict:
        """Return aggregate rental metrics.

        Returns:
            dict: Aggregate totals and revenue values for rentals.
        """
        return Rental.objects.aggregate(
            total_rentals=Count("id"),
            active_rentals=Count("id", filter=Q(returned=False)),
            total_revenue=Sum("total_cost"),
        )
