"""Customer / auth URL patterns."""

from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from customers.views import MeView, RegisterView


@extend_schema(tags=["Auth"])
class AuthTokenObtainPairView(TokenObtainPairView):
    """JWT login endpoint grouped with the rest of the auth docs."""


@extend_schema(tags=["Auth"])
class AuthTokenRefreshView(TokenRefreshView):
    """JWT refresh endpoint grouped with the rest of the auth docs."""


urlpatterns = [
    path("register/", RegisterView.as_view(), name="customer-register"),
    path("token/", AuthTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", AuthTokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="customer-me"),
]
