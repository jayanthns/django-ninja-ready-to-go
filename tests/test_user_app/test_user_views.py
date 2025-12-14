import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.http import HttpRequest

from apps.users_app.v1.schemas import UserCreateSchema, UserSchema
from apps.users_app.v1.views import get_user, register_user


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

        mock_user_service.create = AsyncMock(return_value=user_data)

        resp = await register_user(req, payload)

        assert resp["data"] == user_data
        assert "trace_id" in resp
        assert resp["error"] == {}
        mock_user_service.create.assert_awaited_with(payload)

        # Verify Logs
        assert req.logger.info.call_count == 5
        req.logger.info.assert_any_call("[1] Entering register_user endpoint")
        req.logger.info.assert_any_call(f"[2] Creating new user: {payload.email}")
        req.logger.info.assert_any_call("[3] Calling UserService.create")
        req.logger.info.assert_any_call(f"[4] User created successfully: {user_id}")
        req.logger.info.assert_any_call("[5] Exiting register_user endpoint")

    @patch("apps.users_app.v1.views.UserService")
    async def test_register_user_exception(self, mock_user_service):
        req = await self._make_request()
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")

        mock_user_service.create = AsyncMock(side_effect=Exception("Registration failed"))

        with pytest.raises(Exception) as exc:
            await register_user(req, payload)

        assert "Registration failed" in str(exc.value)

        # Verify Logs
        assert req.logger.info.call_count == 3
        req.logger.info.assert_any_call("[1] Entering register_user endpoint")
        req.logger.info.assert_any_call(f"[2] Creating new user: {payload.email}")
        req.logger.info.assert_any_call("[3] Calling UserService.create")

        req.logger.exception.assert_called_once()
        args, _ = req.logger.exception.call_args
        assert "[Error] Failed to register user" in args[0]

    @patch("apps.users_app.v1.views.UserService")
    async def test_get_user_success(self, mock_user_service):
        req = await self._make_request()
        user_id = uuid.uuid4()

        user_data = UserSchema(id=user_id, username="testuser", email="test@example.com")

        mock_user_service.get = AsyncMock(return_value=user_data)

        status, resp = await get_user(req, user_id)

        assert status == 200
        assert resp["data"] == user_data
        mock_user_service.get.assert_awaited_with(user_id)

        # Verify Logs
        assert req.logger.info.call_count == 4
        req.logger.info.assert_any_call(f"[1] Entering get_user endpoint for ID: {user_id}")
        req.logger.info.assert_any_call("[2] Calling UserService.get")
        req.logger.info.assert_any_call("[3] User found")
        req.logger.info.assert_any_call("[4] Exiting get_user endpoint")

    @patch("apps.users_app.v1.views.UserService")
    async def test_get_user_not_found(self, mock_user_service):
        req = await self._make_request()
        user_id = uuid.uuid4()

        mock_user_service.get = AsyncMock(return_value=None)

        status, resp = await get_user(req, user_id)

        assert status == 404
        assert resp["error"] == {"message": "User not found"}
        mock_user_service.get.assert_awaited_with(user_id)

        # Verify Logs
        # Info calls: [1], [2], [4] Exiting (Not Found) -> 3 calls
        # Warning calls: [3] User not found -> 1 call
        assert req.logger.info.call_count == 3
        req.logger.info.assert_any_call(f"[1] Entering get_user endpoint for ID: {user_id}")
        req.logger.info.assert_any_call("[2] Calling UserService.get")
        req.logger.info.assert_any_call("[4] Exiting get_user endpoint (Not Found)")

        req.logger.warning.assert_called_once_with(f"[3] User not found: {user_id}")

    @patch("apps.users_app.v1.views.UserService")
    async def test_get_user_exception(self, mock_user_service):
        req = await self._make_request()
        user_id = uuid.uuid4()

        mock_user_service.get = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc:
            await get_user(req, user_id)

        assert "Database error" in str(exc.value)

        # Verify Logs (Before exception bubbling up)
        # [1], [2]
        assert req.logger.info.call_count == 2
        req.logger.info.assert_any_call(f"[1] Entering get_user endpoint for ID: {user_id}")
        req.logger.info.assert_any_call("[2] Calling UserService.get")
