"""API views for the rewards domain."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsSelfByEmailOrStaff
from rewards.mixins import RewardHistoryMixin
from rewards.serializers import (
    RewardRedeemSerializer,
    RewardSummarySerializer,
    RewardTransactionDetailSerializer,
    RewardTransactionSerializer,
)
from rewards.services import RewardService

_reward_service = RewardService()

_HISTORY_PARAMETERS = [
    OpenApiParameter(
        name="type",
        description="Optional transaction type filter. Allowed values: earned, redeemed.",
        required=False,
        type=str,
    ),
    OpenApiParameter(
        name="ordering",
        description=(
            "Optional ordering. Allowed values: created_at, points, type. "
            "Prefix with '-' for descending order."
        ),
        required=False,
        type=str,
    ),
    OpenApiParameter(
        name="format",
        description="Optional export format. Allowed values: csv, pdf.",
        required=False,
        type=str,
    ),
]


@extend_schema(tags=["Rewards"])
class RewardSummaryView(APIView):
    """Retrieve the authenticated customer's reward summary."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: RewardSummarySerializer})
    def get(self, request: Request) -> Response:
        """Return the reward summary for the authenticated user."""
        return Response({"data": _reward_service.get_customer_summary(request.user)})


@extend_schema(tags=["Rewards"])
class RewardHistoryView(RewardHistoryMixin, ListAPIView):
    """List the authenticated customer's reward transaction history."""

    permission_classes = (IsAuthenticated,)
    serializer_class = RewardTransactionSerializer

    @extend_schema(parameters=_HISTORY_PARAMETERS, responses={200: RewardTransactionSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """Return paginated reward history for the authenticated user."""
        export, filtered = self.apply_filters_or_export(
            _reward_service.get_customer_history(request.user), request.user.email
        )
        if export is not None:
            return export
        self._filtered_queryset = filtered
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # pragma: no cover
            return _reward_service.empty_history()
        return getattr(self, "_filtered_queryset", _reward_service.get_customer_history(self.request.user))


@extend_schema(tags=["Rewards"])
class RewardTransactionDetailView(APIView):
    """Retrieve full details of a single reward transaction."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: RewardTransactionDetailSerializer})
    def get(self, request: Request, transaction_id) -> Response:
        """Return the transaction detail visible to the authenticated user."""
        transaction = _reward_service.get_transaction_detail(transaction_id, request.user)
        return Response({"data": RewardTransactionDetailSerializer(transaction).data})


@extend_schema(tags=["Rewards"])
class CustomerRewardSummaryView(APIView):
    """Retrieve reward summary for a customer by email — staff or self."""

    permission_classes = (IsSelfByEmailOrStaff,)

    @extend_schema(responses={200: RewardSummarySerializer})
    def get(self, request: Request, customer_email: str) -> Response:
        """Return the reward summary for the given customer email."""
        return Response({"data": _reward_service.get_customer_summary_by_email(customer_email)})


@extend_schema(tags=["Rewards"])
class CustomerRewardHistoryView(RewardHistoryMixin, ListAPIView):
    """List reward history for a customer by email — staff or self."""

    permission_classes = (IsSelfByEmailOrStaff,)
    serializer_class = RewardTransactionSerializer

    @extend_schema(parameters=_HISTORY_PARAMETERS, responses={200: RewardTransactionSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """Return paginated reward history for the given customer email."""
        email = self.kwargs["customer_email"]
        export, filtered = self.apply_filters_or_export(
            _reward_service.get_customer_history_by_email(email), email
        )
        if export is not None:
            return export
        self._filtered_queryset = filtered
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # pragma: no cover
            return _reward_service.empty_history()
        email = self.kwargs["customer_email"]
        return getattr(self, "_filtered_queryset", _reward_service.get_customer_history_by_email(email))


@extend_schema(tags=["Rewards"])
class CustomerRewardSummaryByIdView(APIView):
    """Retrieve reward summary for a customer by identifier — admin only."""

    permission_classes = (IsAdminUser,)

    @extend_schema(responses={200: RewardSummarySerializer})
    def get(self, request: Request, customer_id) -> Response:
        """Return the reward summary for the given customer identifier."""
        customer = _reward_service.resolve_customer_by_id(customer_id)
        return Response({"data": _reward_service.get_customer_summary(customer)})


@extend_schema(tags=["Rewards"])
class CustomerRewardHistoryByIdView(RewardHistoryMixin, ListAPIView):
    """List reward history for a customer by identifier — admin only."""

    permission_classes = (IsAdminUser,)
    serializer_class = RewardTransactionSerializer

    @extend_schema(parameters=_HISTORY_PARAMETERS, responses={200: RewardTransactionSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """Return paginated reward history for the given customer identifier."""
        customer = _reward_service.resolve_customer_by_id(self.kwargs["customer_id"])
        export, filtered = self.apply_filters_or_export(
            _reward_service.get_customer_history(customer), customer.email
        )
        if export is not None:
            return export
        self._filtered_queryset = filtered
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # pragma: no cover
            return _reward_service.empty_history()
        customer = _reward_service.resolve_customer_by_id(self.kwargs["customer_id"])
        return getattr(self, "_filtered_queryset", _reward_service.get_customer_history(customer))


@extend_schema(tags=["Rewards"])
class RewardRedeemView(APIView):
    """Redeem reward points against a rental."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(request=RewardRedeemSerializer, responses={200: RewardTransactionSerializer})
    def post(self, request: Request) -> Response:
        """Apply a point redemption discount to the specified rental."""
        serializer = RewardRedeemSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if request.user.is_staff:
            customer = _reward_service.resolve_customer_by_email(data["customer_email"])
        else:
            customer = request.user

        transaction = _reward_service.redeem_points(
            rental_id=data["rental_id"],
            customer=customer,
            points_to_redeem=data["points_to_redeem"],
        )
        return Response(
            {"data": RewardTransactionSerializer(transaction).data},
            status=status.HTTP_200_OK,
        )
