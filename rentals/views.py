"""API views for the rentals domain."""

from typing import cast

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from core.mixins import CustomerScopedQuerysetMixin
from core.permissions import IsSelfByEmailOrStaff, assert_customer_email_allowed
from customers.models import Customer
from rentals.serializers import RentalCreateSerializer, RentalSerializer, RentalStatsSerializer
from rentals.services import RentalService

_rental_service = RentalService()


@extend_schema(tags=["Rentals"])
class RentalCreateView(GenericAPIView):
    """Create a rental.

    Creates a rental for the authenticated customer. Staff users may also
    create rentals on behalf of another customer by providing customer data.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = RentalCreateSerializer

    @extend_schema(
        request=RentalCreateSerializer,
        responses={201: RentalSerializer},
        examples=[
            OpenApiExample(
                "Create rental",
                value={
                    "car_id": "0192d5e0-7a1a-7b3a-8c4d-1234567890ab",
                    "customer_name": "John Doe",
                    "customer_email": "john@example.com",
                    "days": 5,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request: Request) -> Response:
        """Create a rental and return the created record."""
        actor = cast(Customer, request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        customer_email = data.get("customer_email") or actor.email
        customer_name = data.get("customer_name") or _rental_service.display_name(actor)

        if not actor.is_staff:
            assert_customer_email_allowed(request, customer_email)
            customer = actor
        else:
            customer = _rental_service.resolve_customer(
                customer_email, customer_name, is_staff=True
            )
            if customer is None:
                raise RuntimeError("Staff customer resolution unexpectedly returned None.")

        rental = _rental_service.create_rental(
            car_id=data["car_id"],
            customer=customer,
            customer_name=customer_name,
            customer_email=customer.email,
            days=data["days"],
        )
        return Response({"data": RentalSerializer(rental).data}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Rentals"])
class RentalReturnView(GenericAPIView):
    """Return a rental.

    Marks an active rental as returned, releases the car back to the fleet, and
    triggers reward point calculation.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = RentalSerializer

    @extend_schema(request=None, responses={200: RentalSerializer})
    def post(self, request: Request, rental_id) -> Response:
        """Return a rental by its identifier."""
        result = _rental_service.return_rental(rental_id, actor=cast(Customer, request.user))
        return Response({"data": RentalSerializer(result.rental).data}, status=status.HTTP_200_OK)


@extend_schema(tags=["Rentals"])
class RentalDetailView(GenericAPIView):
    """Retrieve rental details.

    Returns the full details of a single rental. Customers may access only
    their own rentals, while staff users may access any rental.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = RentalSerializer

    @extend_schema(responses={200: RentalSerializer})
    def get(self, request: Request, rental_id) -> Response:
        """Return a single rental visible to the authenticated user."""
        rental = _rental_service.get_visible_rental(rental_id, actor=cast(Customer, request.user))
        return Response({"data": RentalSerializer(rental).data}, status=status.HTTP_200_OK)


@extend_schema(tags=["Rentals"])
class RentalListView(CustomerScopedQuerysetMixin, ListAPIView):
    """List visible rentals.

    Returns a paginated list of rentals visible to the authenticated user.
    Customers see only their own rentals, while staff users see all rentals.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = RentalSerializer

    def get_queryset(self):
        """Return the rentals visible to the authenticated user."""
        if getattr(self, "swagger_fake_view", False):
            return _rental_service.empty_list()
        return self.scope_queryset_to_customer(_rental_service.list_all())


@extend_schema(tags=["Rentals"])
class CustomerRentalListView(ListAPIView):
    """List rentals by customer email.

    Returns a paginated list of rentals for the customer identified by the
    email in the URL. Customers may access only their own data; staff users may
    access any customer.
    """

    permission_classes = (IsSelfByEmailOrStaff,)
    serializer_class = RentalSerializer

    def get_queryset(self):
        """Return rentals for the customer email in the route."""
        if getattr(self, "swagger_fake_view", False):
            return _rental_service.empty_list()
        return _rental_service.list_by_customer_email(self.kwargs["customer_email"])


@extend_schema(tags=["Rentals"])
class CustomerRentalListByIdView(ListAPIView):
    """List rentals by customer identifier.

    Returns a paginated list of rentals for the customer identified by the id
    in the URL.

    This endpoint is restricted to admin users.
    """

    permission_classes = (IsAdminUser,)
    serializer_class = RentalSerializer

    def get_queryset(self):
        """Return rentals for the customer identifier in the route."""
        if getattr(self, "swagger_fake_view", False):
            return _rental_service.empty_list()
        return _rental_service.list_by_customer_id(self.kwargs["customer_id"])


@extend_schema(tags=["Rentals"])
class RentalStatsView(GenericAPIView):
    """Retrieve rental statistics.

    Returns aggregate rental metrics for administrative monitoring and
    reporting.

    This endpoint is restricted to admin users.
    """

    permission_classes = (IsAdminUser,)
    serializer_class = RentalStatsSerializer

    @extend_schema(responses={200: RentalStatsSerializer})
    def get(self, request: Request) -> Response:
        """Return aggregate rental statistics."""
        return Response({"data": _rental_service.get_stats()}, status=status.HTTP_200_OK)
