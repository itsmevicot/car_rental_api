"""Django admin configuration for rental models."""

from django import forms
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from cars.repositories import CarRepository
from rentals.models import Rental
from rentals.services import RentalService

_car_repo = CarRepository()
_rental_service = RentalService()


class RentalAdminAddForm(forms.ModelForm):
    """Admin form used when creating rentals manually."""

    days = forms.IntegerField(
        min_value=1,
        help_text="Number of rental days. Pricing and end date are computed automatically.",
    )

    class Meta:
        model = Rental
        fields = ("car", "customer", "days")


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    """Admin interface for browsing rental records."""

    list_display = [
        "id",
        "car",
        "customer_name",
        "customer_email",
        "start_date",
        "end_date",
        "returned",
    ]
    list_filter = ["returned", "start_date"]
    search_fields = [
        "id",
        "customer_name",
        "customer_email",
        "customer__email",
        "customer__first_name",
        "customer__last_name",
        "car__brand",
        "car__model",
    ]
    autocomplete_fields = ["car", "customer"]
    date_hierarchy = "start_date"
    readonly_fields = ["id", "created_at", "updated_at"]
    fields = [
        "id",
        "car",
        "customer",
        "customer_name",
        "customer_email",
        "start_date",
        "end_date",
        "subtotal",
        "duration_discount",
        "reward_discount",
        "total_cost",
        "returned",
        "actual_return_date",
        "late_fee",
        "created_at",
        "updated_at",
    ]

    def get_form(self, request: HttpRequest, obj: Rental | None = None, **kwargs):
        """Return the admin form used for add or change flows.

        Args:
            request: Current admin request.
            obj: Rental being edited, or ``None`` during creation.
            **kwargs: Extra form configuration forwarded by Django.

        Returns:
            type[forms.ModelForm]: Form class to render in the admin UI.
        """
        if obj is None:
            kwargs["form"] = RentalAdminAddForm
        form = super().get_form(request, obj, **kwargs)
        if obj is None and "car" in form.base_fields:
            form.base_fields["car"].queryset = _car_repo.list_available()
        return form

    def get_readonly_fields(
        self, request: HttpRequest, obj: Rental | None = None
    ) -> list[str] | tuple[str, ...]:
        """Return fields that cannot be edited in the admin form.

        Args:
            request: Current admin request.
            obj: Rental being edited, or ``None`` during creation.

        Returns:
            list[str] | tuple[str, ...]: Read-only field names for the current view.
        """
        if obj is None:
            return []
        return super().get_readonly_fields(request, obj)

    def get_fields(self, request: HttpRequest, obj: Rental | None = None) -> list[str]:
        """Return the field layout for add and change screens.

        Args:
            request: Current admin request.
            obj: Rental being edited, or ``None`` during creation.

        Returns:
            list[str]: Ordered field names for the rendered form.
        """
        if obj is None:
            return ["car", "customer", "days"]
        return list(super().get_fields(request, obj))

    def get_queryset(self, request: HttpRequest) -> QuerySet[Rental]:
        """Return the rental queryset rendered by the changelist.

        Args:
            request: Current admin request.

        Returns:
            QuerySet[Rental]: Queryset optimized for related-object rendering.
        """
        return super().get_queryset(request).select_related("car", "customer")

    def save_form(self, request: HttpRequest, form: forms.ModelForm, change: bool) -> Rental:
        """Create rentals through the domain service during admin adds.

        Args:
            request: Current admin request.
            form: Validated admin form instance.
            change: Whether the operation is editing an existing rental.

        Returns:
            Rental: Persisted rental record.
        """
        if change:
            return super().save_form(request, form, change)

        customer = form.cleaned_data["customer"]
        car = form.cleaned_data["car"]
        days = form.cleaned_data["days"]
        customer_name = _rental_service.display_name(customer)
        return _rental_service.create_rental(
            car_id=car.id,
            customer=customer,
            customer_name=customer_name,
            customer_email=customer.email,
            days=days,
        )

    def save_model(
        self, request: HttpRequest, obj: Rental, form: forms.ModelForm, change: bool
    ) -> None:
        """Persist changes to existing rentals.

        Args:
            request: Current admin request.
            obj: Rental being saved.
            form: Bound admin form.
            change: Whether the operation is editing an existing rental.
        """
        if change:
            super().save_model(request, obj, form, change)
