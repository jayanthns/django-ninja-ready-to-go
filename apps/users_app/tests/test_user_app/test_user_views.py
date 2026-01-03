import uuid
from unittest.mock import AsyncMock, call, MagicMock, patch

import pytest
from django.db import IntegrityError
from django.http import HttpRequest

from apps.users_app.v1.schemas import (
    ResetPasswordConfirmSchema,
    ResetPasswordRequestSchema,
    UserCreateSchema,
    UserSchema,
    VerifyOTPSchema,
)
from apps.users_app.v1.views import (
    register_user,
    reset_password_confirm,
    reset_password_request,
    verify_email,
)


@pytest.mark.asyncio
class TestUserViews:
    async def _make_request(self):
        """Mock a minimal Django request."""
        mock = MagicMock(spec=HttpRequest)
        mock.trace_id = uuid.uuid4()
        mock.logger = MagicMock()
        return mock

    @patch("apps.users_app.v1.views.UserService")
    async def test_register_user_success(self, mock_user_service):
        req = await self._make_request()
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")

        user_id = uuid.uuid4()
        user_data = UserSchema(id=user_id, username="testuser", email="test@example.com")

        mock_user_service.register = AsyncMock(return_value=user_data)

        info_calls = [
            call("[1] Entering register_user endpoint"),
            call(f"[2] Attempting to register user with email: {payload.email}"),
            call("[3] User registered successfully"),
            call("[4] Exiting register_user endpoint"),
        ]

        status, resp = await register_user(req, payload)

        assert resp["data"] == user_data
        assert "trace_id" in resp
        assert resp["error"] == {}
        mock_user_service.register.assert_awaited_with(payload.model_dump())

        # Verify Logs
        assert req.logger.info.call_count == 4
        req.logger.info.assert_has_calls(info_calls)

    @patch("apps.users_app.v1.views.UserService")
    async def test_register_user_exception(self, mock_user_service):
        req = await self._make_request()
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")

        info_calls = [
            call("[1] Entering register_user endpoint"),
            call(f"[2] Attempting to register user with email: {payload.email}"),
            call("[4] Exiting register_user endpoint with error"),
        ]

        error_calls = [call("[3] Registration failed with exception: Registration failed")]

        mock_user_service.register = AsyncMock(side_effect=Exception("Registration failed"))

        await register_user(req, payload)

        # Verify Logs
        assert req.logger.info.call_count == 3
        assert req.logger.error.call_count == 1
        req.logger.info.assert_has_calls(info_calls)
        req.logger.error.assert_has_calls(error_calls)

    @patch("apps.users_app.v1.views.UserService")
    @pytest.mark.parametrize(
        "error_text, expected_field, expected_message",
        [
            ("Email already registered", "email", "Email 'test@example.com' already registered."),
            ("username already exists", "username", "Username 'testuser' already exists."),
            ("Unknown constraint", "unknown", "A unique constraint failed. Please try again."),
        ],
    )
    async def test_register_user_integrity_error(
        self, mock_user_service, error_text, expected_field, expected_message
    ):
        req = await self._make_request()
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")

        mock_user_service.register = AsyncMock(side_effect=IntegrityError(error_text))

        status, resp = await register_user(req, payload)

        assert status == 400
        assert resp["error"]["field"] == expected_field
        assert resp["error"]["message"] == expected_message
        assert resp["data"] is None
        mock_user_service.register.assert_awaited_with(payload.model_dump())

        # Verify Logs
        assert req.logger.info.call_count == 3
        req.logger.warning.assert_called_once_with(f"[3] Registration failed - {expected_message}")

    @patch("apps.users_app.v1.views.User")
    @patch("apps.users_app.v1.views.UserService")
    async def test_verify_email_success(self, mock_user_service, mock_user_model):
        req = await self._make_request()
        payload = VerifyOTPSchema(email="test@example.com", code="123456")

        mock_user = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=mock_user)
        mock_user_model.objects.filter.return_value = mock_queryset

        mock_user_service.verify_otp = AsyncMock(return_value=True)

        status, resp = await verify_email(req, payload)

        assert status == 200
        assert resp["data"]["verified"] is True
        mock_user_model.objects.filter.assert_called_with(email=payload.email)
        mock_user_service.verify_otp.assert_awaited_with(
            user=mock_user,
            code=payload.code,
            purpose="verify_email",
        )

    @patch("apps.users_app.v1.views.User")
    @patch("apps.users_app.v1.views.UserService")
    async def test_verify_email_fail_invalid_otp(self, mock_user_service, mock_user_model):
        req = await self._make_request()
        payload = VerifyOTPSchema(email="test@example.com", code="123456")

        mock_user = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=mock_user)
        mock_user_model.objects.filter.return_value = mock_queryset

        mock_user_service.verify_otp = AsyncMock(return_value=False)

        status, resp = await verify_email(req, payload)

        assert status == 400
        assert resp["error"]["message"] == "Invalid or expired OTP"

    @patch("apps.users_app.v1.views.User")
    @patch("apps.users_app.v1.views.UserService")
    async def test_verify_email_user_not_found(self, mock_user_service, mock_user_model):
        req = await self._make_request()
        payload = VerifyOTPSchema(email="unknown@example.com", code="123456")

        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=None)
        mock_user_model.objects.filter.return_value = mock_queryset

        status, resp = await verify_email(req, payload)

        assert status == 400
        # Check actual error message later if needed
        mock_user_service.verify_otp.assert_not_called()

    @patch("apps.users_app.v1.views.UserService")
    async def test_reset_password_request(self, mock_user_service):
        req = await self._make_request()
        payload = ResetPasswordRequestSchema(email="test@example.com")
        mock_user_service.initiate_password_reset = AsyncMock()

        status, resp = await reset_password_request(req, payload)

        assert status == 200
        assert resp["data"]["status"] == "ok"
        mock_user_service.initiate_password_reset.assert_awaited_with(payload.email)

    @patch("apps.users_app.v1.views.User")
    @patch("apps.users_app.v1.views.UserService")
    async def test_reset_password_confirm_success(self, mock_user_service, mock_user_model):
        req = await self._make_request()
        payload = ResetPasswordConfirmSchema(email="test@example.com", code="123456", new_password="newpass")

        mock_user = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=mock_user)
        mock_user_model.objects.filter.return_value = mock_queryset

        mock_user_service.reset_password = AsyncMock(return_value=True)

        status, resp = await reset_password_confirm(req, payload)

        assert status == 200
        assert resp["data"]["password_reset"] is True
        mock_user_service.reset_password.assert_awaited_with(
            user=mock_user,
            code=payload.code,
            new_password=payload.new_password,
        )

    @patch("apps.users_app.v1.views.User")
    @patch("apps.users_app.v1.views.UserService")
    async def test_reset_password_confirm_fail(self, mock_user_service, mock_user_model):
        req = await self._make_request()
        payload = ResetPasswordConfirmSchema(email="test@example.com", code="123456", new_password="newpass")

        mock_user = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=mock_user)
        mock_user_model.objects.filter.return_value = mock_queryset

        mock_user_service.reset_password = AsyncMock(return_value=False)

        status, resp = await reset_password_confirm(req, payload)

        assert status == 400
        assert resp["error"]["message"] == "Invalid or expired OTP"

    @patch("apps.users_app.v1.views.User")
    @patch("apps.users_app.v1.views.UserService")
    async def test_reset_password_confirm_user_not_found(self, mock_user_service, mock_user_model):
        req = await self._make_request()
        payload = ResetPasswordConfirmSchema(
            email="unknown@example.com", code="123456", new_password="newpass"
        )

        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=None)
        mock_user_model.objects.filter.return_value = mock_queryset

        status, resp = await reset_password_confirm(req, payload)

        assert status == 400
        # assert resp["password_reset"] is False # Structure is different on error
        mock_user_service.reset_password.assert_not_called()
