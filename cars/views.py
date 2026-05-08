"""API views for the cars domain."""

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cars.serializers import CarSerializer
from cars.services import CarService
from core.exceptions import AuthorizationError

_car_service = CarService()


def _is_staff_request(request: Request) -> bool:
    """Return whether the current request belongs to a staff user.

    Args:
        request: Current DRF request.

    Returns:
        bool: ``True`` when the request is authenticated as staff.
    """
    user = request.user
    return bool(user and user.is_authenticated and user.is_staff)


def _wants_unavailable(request: Request) -> bool:
    """Return whether the caller asked to include unavailable cars.

    Args:
        request: Current DRF request.

    Returns:
        bool: ``True`` when the query parameter explicitly enables the flag.
    """
    value = request.query_params.get("include_unavailable", "")
    return value.lower() in {"1", "true", "yes", "on"}


@extend_schema(
    tags=["Cars"],
    parameters=[
        OpenApiParameter(
            name="include_unavailable",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Include unavailable cars in the paginated response. "
                "This parameter is restricted to staff users."
            ),
        )
    ],
)
class CarListView(ListAPIView):
    """List available cars.

    Returns a paginated list of cars that are currently available for rental.
    Unavailable cars are excluded from the public catalog by default.

    This endpoint is public. Staff users can include unavailable cars by
    sending ``include_unavailable=true``.
    """

    permission_classes = (AllowAny,)
    serializer_class = CarSerializer

    def get_queryset(self):
        """Return the fleet visible to the current caller."""
        if getattr(self, "swagger_fake_view", False):
            return _car_service.empty_list()
        if _wants_unavailable(self.request):
            if not _is_staff_request(self.request):
                raise AuthorizationError()
            return _car_service.list_all()
        return _car_service.list_available()


@extend_schema(tags=["Cars"])
class CarDetailView(APIView):
    """Retrieve car details.

    Returns the public details of a single car, including its category and
    daily rental rate. Unavailable cars are hidden from non-staff callers and
    return ``404 Not Found``.

    This endpoint is public. Staff users can retrieve unavailable cars.
    """

    permission_classes = (AllowAny,)
    serializer_class = CarSerializer

    @extend_schema(responses={200: CarSerializer})
    def get(self, request: Request, car_id):
        """Return the details of a single car by its identifier."""
        car = (
            _car_service.get_by_id(car_id)
            if _is_staff_request(request)
            else _car_service.get_available_by_id(car_id)
        )
        return Response({"data": CarSerializer(car).data})
