"""Mixins for reward views."""

from __future__ import annotations

from django.http import HttpResponse

from rewards.exporters import csv_response, pdf_response
from rewards.serializers import HistoryQueryParamsSerializer
from rewards.services import RewardService

_reward_service = RewardService()


class RewardHistoryMixin:
    """Shared behaviour for history list views.

    Validates query parameters, applies filters, and handles CSV/PDF export
    before handing off to the standard paginated list flow.
    """

    def parse_history_params(self) -> dict:
        serializer = HistoryQueryParamsSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def apply_filters_or_export(self, queryset, email: str) -> tuple[HttpResponse | None, object]:
        params = self.parse_history_params()
        queryset = _reward_service.filter_history(
            queryset,
            type_filter=params.get("type"),
            ordering=params.get("ordering"),
        )
        fmt = params.get("format")
        if fmt == "csv":
            return csv_response(queryset, email), None
        if fmt == "pdf":
            return pdf_response(list(queryset), email), None
        return None, queryset
