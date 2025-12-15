import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from common.services import BaseCRUDService

from .models import User, UserOTP


class UserService(BaseCRUDService):
    model = User

    # ----------------------------
    # Registration
    # ----------------------------
    @classmethod
    async def register(cls, data):
        if isinstance(data, dict) and "password" in data:
            data["password"] = make_password(data["password"])

        user = await cls.create(data)

        await cls._generate_otp(
            user=user,
            purpose="verify_email",
        )

        # TODO: send email notification
        return user

    # ----------------------------
    # OTP helpers
    # ----------------------------
    @staticmethod
    async def _generate_otp(user: User, purpose: str) -> UserOTP:
        code = f"{random.randint(100000, 999999)}"

        otp = await UserOTP.objects.acreate(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        # TEMP: print instead of notification
        print(f"\n{'=' * 50}\n[OTP] {purpose} for {user.email}: {code}\n{'=' * 50}\n")

        return otp

    @staticmethod
    async def verify_otp(user: User, code: str, purpose: str) -> bool:
        otp = (
            await UserOTP.objects.filter(
                user=user,
                code=code,
                purpose=purpose,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .select_related("user")
            .afirst()
        )

        if not otp:
            return False

        otp.is_used = True
        await otp.asave(update_fields=["is_used"])

        if purpose == "verify_email":
            user.is_verified = True
            user.verified_at = timezone.now()
            await user.asave(update_fields=["is_verified", "verified_at"])

        return True

    # ----------------------------
    # Authentication check helper
    # ----------------------------
    @staticmethod
    def auth_warning(user: User) -> str | None:
        if not user.is_verified:
            return "Email not verified"
        return None

    # ----------------------------
    # Reset password flow
    # ----------------------------
    @staticmethod
    async def initiate_password_reset(email: str):
        user = await User.objects.filter(email=email).afirst()
        if not user:
            return  # silent fail (security)

        await UserService._generate_otp(
            user=user,
            purpose="reset_password",
        )

    @staticmethod
    async def reset_password(user: User, code: str, new_password: str) -> bool:
        valid = await UserService.verify_otp(
            user=user,
            code=code,
            purpose="reset_password",
        )
        if not valid:
            return False

        user.set_password(new_password)
        await user.asave(update_fields=["password"])
        return True
