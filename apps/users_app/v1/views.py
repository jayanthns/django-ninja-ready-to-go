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
    request.logger.info("[1] Entering register_user endpoint")
    request.logger.info(f"[2] Creating new user: {payload.email}")

    try:
        request.logger.info("[3] Calling UserService.create")
        data = await UserService.create(payload)

        request.logger.info(f"[4] User created successfully: {data.id}")
        request.logger.info("[5] Exiting register_user endpoint")
        return {"data": data, "trace_id": str(request.trace_id), "error": {}}

    except Exception as e:
        request.logger.exception(f"[Error] Failed to register user: {payload.email} with error: {str(e)}")
        raise


@router.get("/{user_id}/", response=create_api_response_schema(UserSchema))
async def get_user(request: HttpRequest, user_id: uuid.UUID) -> create_api_response_schema(UserSchema):
    """Retrieve a user by ID (Async)."""
    request.logger.info(f"[1] Entering get_user endpoint for ID: {user_id}")
    request.logger.info("[2] Calling UserService.get")

    user = await UserService.get(user_id)
    if not user:
        request.logger.warning(f"[3] User not found: {user_id}")
        request.logger.info("[4] Exiting get_user endpoint (Not Found)")
        return create_api_response_schema(UserSchema)(
            error={"message": "User not found"},
            trace_id=str(request.trace_id),
        )

    request.logger.info("[3] User found")
    request.logger.info("[4] Exiting get_user endpoint")
    return create_api_response_schema(UserSchema)(
        data=user,
        trace_id=str(request.trace_id),
    )
