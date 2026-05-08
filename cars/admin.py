from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from cars.models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    """Admin interface for car records."""

    list_display = ["id", "brand", "model", "year", "daily_rate", "available"]
    list_filter = ["available", "brand"]
    search_fields = ["id", "brand", "model"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet[Car], search_term: str
    ) -> tuple[QuerySet[Car], bool]:
        """Return search results for standard admin and autocomplete flows.

        Args:
            request: Current admin request.
            queryset: Base queryset produced by the admin.
            search_term: Raw search term entered by the user.

        Returns:
            tuple[QuerySet[Car], bool]: Filtered queryset and duplicate flag.
        """
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        if (
            request.path.endswith("/autocomplete/")
            and request.GET.get("app_label") == "rentals"
            and request.GET.get("model_name") == "rental"
            and request.GET.get("field_name") == "car"
        ):
            queryset = queryset.filter(available=True)
        return queryset, may_have_duplicates
