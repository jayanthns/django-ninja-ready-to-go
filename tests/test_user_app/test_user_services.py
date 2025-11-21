from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.users_app.v1.schemas import UserCreateSchema
from apps.users_app.v1.services import UserService


@pytest.mark.asyncio
class TestUserService:
    @patch("apps.users_app.v1.services.User")
    @patch("apps.users_app.v1.services.make_password")
    async def test_create_user(self, mock_make_password, mock_user_model):
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")
        mock_make_password.return_value = "hashed_password"

        mock_created_user = MagicMock()
        mock_created_user.username = "testuser"
        mock_created_user.email = "test@example.com"

        mock_user_model.objects.acreate = AsyncMock(return_value=mock_created_user)

        user = await UserService.create_user(payload)

        assert user == mock_created_user
        mock_make_password.assert_called_with("password123")
        mock_user_model.objects.acreate.assert_awaited_with(
            username="testuser",
            email="test@example.com",
            password="hashed_password",
        )

    @patch("apps.users_app.v1.services.User")
    async def test_get_user_by_id_found(self, mock_user_model):
        user_id = 1
        mock_user = MagicMock()
        mock_user.id = user_id

        # Mock the chain: User.objects.filter().afirst()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=mock_user)
        mock_user_model.objects.filter.return_value = mock_queryset

        user = await UserService.get_user_by_id(user_id)

        assert user == mock_user
        mock_user_model.objects.filter.assert_called_with(id=user_id)
        mock_queryset.afirst.assert_awaited_once()

    @patch("apps.users_app.v1.services.User")
    async def test_get_user_by_id_not_found(self, mock_user_model):
        user_id = 999

        # Mock the chain: User.objects.filter().afirst()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=None)
        mock_user_model.objects.filter.return_value = mock_queryset

        user = await UserService.get_user_by_id(user_id)

        assert user is None
        mock_user_model.objects.filter.assert_called_with(id=user_id)
        mock_queryset.afirst.assert_awaited_once()
