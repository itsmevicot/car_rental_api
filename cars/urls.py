"""Car URL patterns."""

from django.urls import path

from cars.views import CarDetailView, CarListView

urlpatterns = [
    path("", CarListView.as_view(), name="car-list"),
    path("<uuid:car_id>/", CarDetailView.as_view(), name="car-detail"),
]
