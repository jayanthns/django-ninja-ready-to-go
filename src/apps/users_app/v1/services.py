from django.contrib.auth.hashers import make_password

from src.apps.users_app.v1.models import User
from src.apps.users_app.v1.schemas import UserCreateSchema, UserSchema


class UserService:
    @staticmethod
    async def create_user(payload: UserCreateSchema) -> UserSchema:
        """Create a new user asynchronously."""
        user = await User.objects.acreate(
            username=payload.username,
            email=payload.email,
            password=make_password(payload.password),  # Hash the password
        )
        return user
        # return UserSchema.model_validate(user)  # ✅ Convert Django model to Pydantic schema

    @staticmethod
    async def get_user_by_id(user_id: int) -> UserSchema | None:
        """Fetch a user by ID asynchronously."""
        user = await User.objects.filter(id=user_id).afirst()
        return user
        # return UserSchema.model_validate(user) if user else None
