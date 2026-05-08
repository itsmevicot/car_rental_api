"""Rewards URL patterns."""

from django.urls import path

from rewards.views import (
    CustomerRewardHistoryByIdView,
    CustomerRewardHistoryView,
    CustomerRewardSummaryByIdView,
    CustomerRewardSummaryView,
    RewardHistoryView,
    RewardRedeemView,
    RewardSummaryView,
    RewardTransactionDetailView,
)

urlpatterns = [
    path("", RewardSummaryView.as_view(), name="reward-summary"),
    path("history/", RewardHistoryView.as_view(), name="reward-history"),
    path(
        "customer/<str:customer_email>/",
        CustomerRewardSummaryView.as_view(),
        name="customer-reward-summary",
    ),
    path(
        "customer/<str:customer_email>/history/",
        CustomerRewardHistoryView.as_view(),
        name="customer-reward-history",
    ),
    path(
        "customers/<uuid:customer_id>/",
        CustomerRewardSummaryByIdView.as_view(),
        name="customer-reward-summary-by-id",
    ),
    path(
        "customers/<uuid:customer_id>/history/",
        CustomerRewardHistoryByIdView.as_view(),
        name="customer-reward-history-by-id",
    ),
    path("apply/", RewardRedeemView.as_view(), name="reward-redeem"),
    path(
        "transactions/<uuid:transaction_id>/",
        RewardTransactionDetailView.as_view(),
        name="reward-transaction-detail",
    ),
]
