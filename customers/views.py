"""Auth and profile views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.serializers import CustomerRegistrationSerializer, CustomerSerializer


@extend_schema(tags=["Auth"])
class RegisterView(APIView):
    """Register a customer account.

    Creates a new customer profile that can be used to authenticate and access
    customer endpoints.

    This endpoint is public and does not require authentication.
    """

    permission_classes = (AllowAny,)

    @extend_schema(request=CustomerRegistrationSerializer, responses={201: CustomerSerializer})
    def post(self, request: Request) -> Response:
        """Create a new customer account and return the created profile."""
        serializer = CustomerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response({"data": CustomerSerializer(customer).data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Auth"])
class MeView(APIView):
    """Retrieve the authenticated profile.

    Returns the profile of the currently authenticated customer.
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: CustomerSerializer})
    def get(self, request: Request) -> Response:
        """Return the profile of the authenticated customer."""
        return Response({"data": CustomerSerializer(request.user).data})
