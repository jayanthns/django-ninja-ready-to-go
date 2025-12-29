from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from apps.users_app.v1.schemas import UserCreateSchema
from apps.users_app.v1.services import UserService


@pytest.mark.asyncio
class TestUserService:
    @patch("apps.users_app.v1.services.UserService._generate_otp")
    @patch("apps.users_app.v1.services.make_password")
    async def test_create_user(self, mock_make_password, mock_generate_otp):
        payload = UserCreateSchema(username="testuser", email="test@example.com", password="password123")
        mock_make_password.return_value = "hashed_password"

        mock_created_user = MagicMock()
        mock_created_user.username = "testuser"
        mock_created_user.email = "test@example.com"

        mock_user_model = MagicMock()
        mock_user_model.objects.acreate = AsyncMock(return_value=mock_created_user)

        with patch.object(UserService, "model", mock_user_model):
            user = await UserService.register(payload.dict())

        assert user == mock_created_user
        mock_make_password.assert_called_with("password123")
        # Ensure conversion to dict happened and password hashed
        mock_user_model.objects.acreate.assert_awaited_with(
            username="testuser",
            email="test@example.com",
            password="hashed_password",
        )
        mock_generate_otp.assert_awaited_once()

    @patch("apps.users_app.v1.services.UserService._generate_otp")
    @patch("apps.users_app.v1.services.make_password")
    async def test_create_user_with_dict(self, mock_make_password, mock_generate_otp):
        payload = {"username": "testuser", "email": "test@example.com", "password": "password123"}
        mock_make_password.return_value = "hashed_password"

        mock_created_user = MagicMock()
        mock_created_user.username = "testuser"
        mock_created_user.email = "test@example.com"

        mock_user_model = MagicMock()
        mock_user_model.objects.acreate = AsyncMock(return_value=mock_created_user)

        with patch.object(UserService, "model", mock_user_model):
            user = await UserService.register(payload)

        assert user == mock_created_user
        mock_make_password.assert_called_with("password123")
        mock_user_model.objects.acreate.assert_awaited_with(
            username="testuser",
            email="test@example.com",
            password="hashed_password",
        )
        mock_generate_otp.assert_awaited_once()

    async def test_create_user_with_dict_no_password(self):
        payload = {"username": "testuser", "email": "test@example.com"}
        # No password in payload

        mock_created_user = MagicMock()
        mock_created_user.username = "testuser"
        mock_created_user.email = "test@example.com"

        mock_user_model = MagicMock()
        mock_user_model.objects.acreate = AsyncMock(return_value=mock_created_user)

        with patch.object(UserService, "model", mock_user_model):
            user = await UserService.create(payload)

        assert user == mock_created_user
        mock_user_model.objects.acreate.assert_awaited_with(
            username="testuser",
            email="test@example.com",
        )

    async def test_get_user_by_id_found(self):
        user_id = 1
        mock_user = MagicMock()
        mock_user.id = user_id

        # Mock the chain: User.objects.filter().afirst()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=mock_user)

        mock_user_model = MagicMock()
        mock_user_model.objects.filter.return_value = mock_queryset

        with patch.object(UserService, "model", mock_user_model):
            user = await UserService.get(user_id)

        assert user == mock_user
        mock_user_model.objects.filter.assert_called_with(pk=user_id)
        mock_queryset.afirst.assert_awaited_once()

    async def test_get_user_by_id_not_found(self):
        user_id = 999

        # Mock the chain: User.objects.filter().afirst()
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=None)

        mock_user_model = MagicMock()
        mock_user_model.objects.filter.return_value = mock_queryset

        with patch.object(UserService, "model", mock_user_model):
            user = await UserService.get(user_id)

        assert user is None
        mock_user_model.objects.filter.assert_called_with(pk=user_id)
        mock_queryset.afirst.assert_awaited_once()

    @patch("apps.users_app.v1.services.UserOTP")
    async def test_generate_otp(self, mock_user_otp):
        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        mock_otp_instance = MagicMock()
        mock_user_otp.objects.acreate = AsyncMock(return_value=mock_otp_instance)

        with patch("apps.users_app.v1.services.random") as mock_random:
            mock_random.randint.return_value = 123456
            # Mock timezone to use in assertion if strictly needed or use ANY
            # simpler to use a generic matcher for expiry

            otp = await UserService._generate_otp(mock_user, "test_purpose")

            assert otp == mock_otp_instance
            mock_user_otp.objects.acreate.assert_awaited_with(
                user=mock_user, code="123456", purpose="test_purpose", expires_at=ANY
            )

    @patch("apps.users_app.v1.services.UserOTP")
    async def test_verify_otp(self, mock_user_otp):
        mock_user = MagicMock()

        mock_otp_instance = MagicMock()
        mock_otp_instance.asave = AsyncMock()  # Mock asave
        mock_user_otp.objects.filter.return_value.select_related.return_value.afirst = AsyncMock(
            return_value=mock_otp_instance
        )

        # Test Success
        res = await UserService.verify_otp(mock_user, "123456", "test_purpose")
        assert res is True
        mock_otp_instance.asave.assert_awaited()
        mock_otp_instance.asave.assert_awaited()
        assert mock_otp_instance.is_used is True

    @patch("apps.users_app.v1.services.UserOTP")
    async def test_verify_otp_email_purpose(self, mock_user_otp):
        mock_user = MagicMock()
        mock_user.asave = AsyncMock()

        mock_otp_instance = MagicMock()
        mock_otp_instance.asave = AsyncMock()
        mock_user_otp.objects.filter.return_value.select_related.return_value.afirst = AsyncMock(
            return_value=mock_otp_instance
        )

        # Test verify_email specific logic
        res = await UserService.verify_otp(mock_user, "123456", "verify_email")

        assert res is True
        mock_otp_instance.asave.assert_awaited()
        assert mock_user.is_verified is True
        mock_user.asave.assert_awaited()

    @patch("apps.users_app.v1.services.UserOTP")
    async def test_verify_otp_fail(self, mock_user_otp):
        mock_user = MagicMock()

        mock_user_otp.objects.filter.return_value.select_related.return_value.afirst = AsyncMock(
            return_value=None
        )

        res = await UserService.verify_otp(mock_user, "123456", "test_purpose")
        assert res is False

    @patch("apps.users_app.v1.services.UserService._generate_otp")
    @patch("apps.users_app.v1.services.User")
    async def test_initiate_password_reset(self, mock_user_model, mock_generate_otp):
        mock_queryset = MagicMock()
        mock_user = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=mock_user)

        mock_user_model.objects.filter.return_value = mock_queryset

        await UserService.initiate_password_reset("test@example.com")

        mock_generate_otp.assert_awaited_with(user=mock_user, purpose="reset_password")

    @patch("apps.users_app.v1.services.User")
    async def test_initiate_password_reset_user_not_found(self, mock_user_model):
        mock_queryset = MagicMock()
        mock_queryset.afirst = AsyncMock(return_value=None)

        mock_user_model.objects.filter.return_value = mock_queryset

        # Should just return none, no error
        await UserService.initiate_password_reset("unknown@example.com")

    @patch("apps.users_app.v1.services.UserService.verify_otp")
    async def test_reset_password_success(self, mock_verify_otp):
        mock_verify_otp.return_value = True
        mock_user = MagicMock()
        mock_user.asave = AsyncMock()

        res = await UserService.reset_password(mock_user, "123456", "new_pass")

        assert res is True
        mock_user.set_password.assert_called_with("new_pass")
        mock_user.asave.assert_awaited()

    @patch("apps.users_app.v1.services.UserService.verify_otp")
    async def test_reset_password_fail(self, mock_verify_otp):
        mock_verify_otp.return_value = False
        mock_user = MagicMock()

        res = await UserService.reset_password(mock_user, "123456", "new_pass")
        assert res is False
        mock_user.set_password.assert_not_called()

    def test_auth_warning_verified(self):
        user = MagicMock()
        user.is_verified = True
        assert UserService.auth_warning(user) is None

    def test_auth_warning_not_verified(self):
        user = MagicMock()
        user.is_verified = False
        assert UserService.auth_warning(user) == "Email not verified"

    @patch("apps.users_app.v1.services.UserService._generate_otp")
    async def test_register_with_schema(self, mock_generate_otp):
        # Scenario: data is not a dict (e.g. Pydantic schema), so line 20 condition fails (isinstance=False)
        payload = UserCreateSchema(username="testschema", email="schema@test.com", password="raw_password")

        mock_created_user = MagicMock()
        mock_user_model = MagicMock()
        mock_user_model.objects.acreate = AsyncMock(return_value=mock_created_user)

        with patch.object(UserService, "model", mock_user_model):
            # We assert that create is called with the PAYLOAD object, not a dict
            # and that make_password was NOT called (branch skipped)
            await UserService.register(payload)

        mock_user_model.objects.acreate.assert_awaited_with(
            username="testschema", email="schema@test.com", password="raw_password"
        )
        mock_generate_otp.assert_awaited_once()

    @patch("apps.users_app.v1.services.UserService._generate_otp")
    async def test_register_no_password(self, mock_generate_otp):
        # Scenario: data is dict but no password, so line 20 condition fails ("password" in data=False)
        payload = {"username": "nopass", "email": "nopass@test.com"}

        mock_created_user = MagicMock()
        mock_user_model = MagicMock()
        mock_user_model.objects.acreate = AsyncMock(return_value=mock_created_user)

        with patch.object(UserService, "model", mock_user_model):
            await UserService.register(payload)

        mock_user_model.objects.acreate.assert_awaited_with(username="nopass", email="nopass@test.com")
        mock_generate_otp.assert_awaited_once()
