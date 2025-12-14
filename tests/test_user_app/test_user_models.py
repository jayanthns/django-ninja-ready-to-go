from unittest.mock import patch

import pytest

from apps.users_app.v1.models import User


class TestUserModel:

    def test_set_password_hashes_password(self):
        user = User(username="testuser", email="testuser@example.com")
        raw_password = "securepassword123"
        user.set_password(raw_password)
        assert user.check_password(raw_password) is True
        assert user.password != raw_password  # Ensure password is hashed

    def test_check_password_with_incorrect_password(self):
        user = User(username="testuser", email="testuser@example.com")
        raw_password = "securepassword123"
        user.set_password(raw_password)
        assert user.check_password("wrongpassword") is False


class TestUserManager:
    @patch("apps.users_app.v1.models.User.save")
    def test_create_user(self, mock_save):
        user = User.objects.create_user(email="normal@user.com", password="foo", username="normal_user")
        assert user.email == "normal@user.com"
        assert user.check_password("foo")
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
        mock_save.assert_called_once()

    def test_create_user_missing_email(self):
        with pytest.raises(ValueError, match="Email must be set"):
            User.objects.create_user(email="", password="foo", username="no_email_user")

    @patch("apps.users_app.v1.models.User.save")
    def test_create_superuser(self, mock_save):
        admin_user = User.objects.create_superuser(
            email="super@user.com", password="foo", username="super_user"
        )
        assert admin_user.email == "super@user.com"
        assert admin_user.check_password("foo")
        assert admin_user.is_active
        assert admin_user.is_staff
        assert admin_user.is_superuser
        mock_save.assert_called_once()

    def test_create_superuser_missing_is_staff(self):
        with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
            User.objects.create_superuser(
                email="super@user.com", password="foo", username="super_user", is_staff=False
            )

    def test_create_superuser_missing_is_superuser(self):
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
            User.objects.create_superuser(
                email="super@user.com", password="foo", username="super_user", is_superuser=False
            )
