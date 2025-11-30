import pytest

from apps.users_app.v1.models import User


@pytest.mark.asyncio
class TestUserModel:

    async def test_set_password_hashes_password(self):
        user = User(username="testuser", email="testuser@example.com")
        raw_password = "securepassword123"
        await user.set_password(raw_password)
        assert await user.check_password(raw_password) is True
        assert user.password != raw_password  # Ensure password is hashed

    async def test_check_password_with_incorrect_password(self):
        user = User(username="testuser", email="testuser@example.com")
        raw_password = "securepassword123"
        await user.set_password(raw_password)
        assert await user.check_password("wrongpassword") is False
