"""Core URLs (health check)."""

from django.urls import path

from core.views import HealthCheckView, ReadinessView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("ready/", ReadinessView.as_view(), name="readiness-check"),
]
