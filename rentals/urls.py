"""Rental URL patterns."""

from django.urls import path

from rentals.views import (
    CustomerRentalListByIdView,
    CustomerRentalListView,
    RentalCreateView,
    RentalDetailView,
    RentalListView,
    RentalReturnView,
    RentalStatsView,
)

urlpatterns = [
    path("", RentalListView.as_view(), name="rental-list"),
    path("create/", RentalCreateView.as_view(), name="rental-create"),
    path("<uuid:rental_id>/return/", RentalReturnView.as_view(), name="rental-return"),
    path("<uuid:rental_id>/", RentalDetailView.as_view(), name="rental-detail"),
    path("stats/", RentalStatsView.as_view(), name="rental-stats"),
    path(
        "customer/<str:customer_email>/",
        CustomerRentalListView.as_view(),
        name="customer-rental-list",
    ),
    path(
        "customers/<uuid:customer_id>/",
        CustomerRentalListByIdView.as_view(),
        name="customer-rental-list-by-id",
    ),
]
