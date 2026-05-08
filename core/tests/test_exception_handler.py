"""Tests for the centralized exception handling and permissions."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import APIException, ValidationError

from core.exception_handler import custom_exception_handler
from core.exceptions import AuthorizationError, NotFoundError, ServiceError
from core.permissions import IsSelfByEmailOrStaff, assert_customer_email_allowed


class TestCoreExceptionHandler:
    def _context(self) -> dict:
        return {"view": MagicMock(), "request": MagicMock()}

    def test_handles_service_error(self) -> None:
        response = custom_exception_handler(NotFoundError("Car", "123"), self._context())
        assert response is not None
        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_handles_validation_error_with_scalar_detail(self) -> None:
        response = custom_exception_handler(
            ValidationError({"field": "This field is required."}),
            self._context(),
        )
        assert response is not None
        assert response.status_code == 400
        assert response.data["error"]["code"] == "validation_error"

    def test_handles_api_exception_with_dict_detail(self) -> None:
        response = custom_exception_handler(
            APIException(detail={"detail": "forbidden"}),
            self._context(),
        )
        assert response is not None
        assert response.status_code == 500
        assert response.data["error"]["message"] == "forbidden"

    def test_handles_api_exception_with_list_detail(self) -> None:
        response = custom_exception_handler(APIException(detail=["bad"]), self._context())
        assert response is not None
        assert response.status_code == 500
        assert response.data["error"]["message"] == "bad"

    def test_returns_none_for_unhandled(self) -> None:
        assert custom_exception_handler(RuntimeError("unexpected"), self._context()) is None


class TestCorePermissions:
    def test_assert_customer_email_allowed_raises_for_other_email(self) -> None:
        request = MagicMock()
        request.user = SimpleNamespace(is_staff=False, email="john@example.com")
        with pytest.raises(AuthorizationError):
            assert_customer_email_allowed(request, "other@example.com")

    def test_assert_customer_email_allowed_passes_for_staff(self) -> None:
        request = MagicMock()
        request.user = SimpleNamespace(is_staff=True, email="john@example.com")
        assert assert_customer_email_allowed(request, "other@example.com") is None

    def test_permission_denies_unauthenticated(self) -> None:
        permission = IsSelfByEmailOrStaff()
        request = MagicMock()
        request.user = SimpleNamespace(is_authenticated=False)
        view = SimpleNamespace(kwargs={"customer_email": "john@example.com"})
        assert permission.has_permission(request, view) is False

    def test_permission_allows_staff(self) -> None:
        permission = IsSelfByEmailOrStaff()
        request = MagicMock()
        request.user = SimpleNamespace(
            is_authenticated=True, is_staff=True, email="admin@example.com"
        )
        view = SimpleNamespace(kwargs={"customer_email": "john@example.com"})
        assert permission.has_permission(request, view) is True

    def test_permission_allows_owner(self) -> None:
        permission = IsSelfByEmailOrStaff()
        request = MagicMock()
        request.user = SimpleNamespace(
            is_authenticated=True, is_staff=False, email="john@example.com"
        )
        view = SimpleNamespace(kwargs={"customer_email": "JOHN@example.com"})
        assert permission.has_permission(request, view) is True

    def test_permission_raises_for_other_customer(self) -> None:
        permission = IsSelfByEmailOrStaff()
        request = MagicMock()
        request.user = SimpleNamespace(
            is_authenticated=True, is_staff=False, email="john@example.com"
        )
        view = SimpleNamespace(kwargs={"customer_email": "other@example.com"})
        with pytest.raises(AuthorizationError):
            permission.has_permission(request, view)


class TestCoreExceptions:
    def test_service_error_default_attributes(self) -> None:
        err = ServiceError("test message")
        assert err.message == "test message"
        assert err.code == "service_error"
        assert err.status_code == 400
