import uuid

from django.http import HttpRequest, JsonResponse
from ninja import Router

from apps.users_app.v1.schemas import UserCreateSchema, UserSchema
from apps.users_app.v1.services import UserService
from common.base_schemas import create_api_response_schema

router = Router()


@router.post("/register", response=create_api_response_schema(UserSchema))
async def register_user(request: HttpRequest, payload: UserCreateSchema) -> JsonResponse:
    """Register a new user (Async)."""
    data = await UserService.create_user(payload)
    return {"data": data, "trace_id": str(uuid.uuid4()), "error": {}}  # ✅ Fully async


@router.get("/{user_id}/", response=create_api_response_schema(UserSchema))
async def get_user(request: HttpRequest, user_id: uuid.UUID) -> create_api_response_schema(UserSchema):
    """Retrieve a user by ID (Async)."""
    user = await UserService.get_user_by_id(user_id)
    if not user:
        return create_api_response_schema(UserSchema)(
            error={"message": "User not found"},
            trace_id=str(request.trace_id),
        )  # ✅ Properly structured error
    return create_api_response_schema(UserSchema)(
        data=user,
        trace_id=str(request.trace_id),
    )
