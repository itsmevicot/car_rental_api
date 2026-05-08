from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from rewards.models import RewardTransaction


@admin.register(RewardTransaction)
class RewardTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "customer_email",
        "rental_link",
        "type",
        "points",
        "reason",
        "created_at",
    ]
    list_filter = ["type", "created_at"]
    search_fields = ["id", "customer_email", "reason", "rental__id", "rental__customer_email"]
    date_hierarchy = "created_at"
    fields = [
        "id",
        "customer",
        "customer_email",
        "rental_link",
        "type",
        "points",
        "reason",
        "breakdown",
        "idempotency_key",
        "created_at",
    ]
    readonly_fields = [
        "id",
        "customer",
        "customer_email",
        "rental_link",
        "type",
        "points",
        "reason",
        "breakdown",
        "idempotency_key",
        "created_at",
    ]

    @admin.display(description="Rental", ordering="rental__id")
    def rental_link(self, obj: RewardTransaction) -> str:
        """Render a link to the related rental in the admin.

        Args:
            obj: Reward transaction being rendered.

        Returns:
            str: HTML link to the related rental change page.
        """
        url = reverse("admin:rentals_rental_change", args=[obj.rental_id])
        return format_html('<a href="{}">{}</a>', url, obj.rental_id)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
