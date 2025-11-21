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
        return mock

    @patch("apps.users_app.v1.views.UserService")
    async def test_register_user_success(self, mock_user_service):
        req = await self._make_request()
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")

        user_data = UserSchema(id=1, username="testuser", email="test@example.com")

        mock_user_service.create_user = AsyncMock(return_value=user_data)

        resp = await register_user(req, payload)

        assert resp["data"] == user_data
        assert "trace_id" in resp
        assert resp["error"] == {}
        mock_user_service.create_user.assert_awaited_with(payload)

    @patch("apps.users_app.v1.views.UserService")
    async def test_register_user_exception(self, mock_user_service):
        req = await self._make_request()
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")

        mock_user_service.create_user = AsyncMock(side_effect=Exception("Registration failed"))

        with pytest.raises(Exception) as exc:
            await register_user(req, payload)

        assert "Registration failed" in str(exc.value)

    @patch("apps.users_app.v1.views.UserService")
    async def test_get_user_success(self, mock_user_service):
        req = await self._make_request()
        user_id = 1

        user_data = UserSchema(id=user_id, username="testuser", email="test@example.com")

        mock_user_service.get_user_by_id = AsyncMock(return_value=user_data)

        resp = await get_user(req, user_id)

        assert resp.data == user_data
        mock_user_service.get_user_by_id.assert_awaited_with(user_id)

    @patch("apps.users_app.v1.views.UserService")
    async def test_get_user_not_found(self, mock_user_service):
        req = await self._make_request()
        user_id = 999

        mock_user_service.get_user_by_id = AsyncMock(return_value=None)

        resp = await get_user(req, user_id)

        assert resp.error == {"message": "User not found"}
        mock_user_service.get_user_by_id.assert_awaited_with(user_id)

    @patch("apps.users_app.v1.views.UserService")
    async def test_get_user_exception(self, mock_user_service):
        req = await self._make_request()
        user_id = 1

        mock_user_service.get_user_by_id = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception) as exc:
            await get_user(req, user_id)

        assert "Database error" in str(exc.value)
