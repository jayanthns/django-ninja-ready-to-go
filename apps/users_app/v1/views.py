from django.db import IntegrityError
from ninja import Router

from apps.users_app.v1.schemas import (
    ResetPasswordConfirmResponseSchema,
    ResetPasswordConfirmSchema,
    ResetPasswordRequestResponseSchema,
    ResetPasswordRequestSchema,
    UserCreateResponseSchema,
    UserCreateSchema,
    UserSchema,
    VerifyOTPResponseSchema,
    VerifyOTPSchema,
)
from apps.users_app.v1.services import UserService
from common.base_schemas import create_api_response_schema

from .models import User

router = Router()


@router.post(
    "/register",
    response={
        200: create_api_response_schema(UserCreateResponseSchema),
        400: create_api_response_schema(UserCreateResponseSchema),
        # TODO Pass an example of how to use the dynamic response schema
    },
)
async def register_user(request, payload: UserCreateSchema):
    request.logger.info("[1] Entering register_user endpoint")
    try:
        request.logger.info(f"[2] Attempting to register user with email: {payload.email}")
        user = await UserService.register(payload.model_dump())
        request.logger.info("[3] User registered successfully")
        request.logger.info("[4] Exiting register_user endpoint")
        return 200, {"data": user, "trace_id": str(request.trace_id), "error": {}}
    except IntegrityError:
        request.logger.warning(f"[3] Registration failed: Email {payload.email} already exists")
        request.logger.info("[4] Exiting register_user endpoint with error")
        return 400, {
            "error": {"message": "Email already registered"},
            "trace_id": str(request.trace_id),
            "data": None,
        }
    except Exception as e:
        request.logger.error(f"[3] Registration failed with exception: {e}")
        request.logger.info("[4] Exiting register_user endpoint with error")
        return 400, {
            "error": {"message": "Registration failed"},
            "trace_id": str(request.trace_id),
            "data": None,
        }


@router.post(
    "/verify-email",
    response={
        200: create_api_response_schema(VerifyOTPResponseSchema),
        400: create_api_response_schema(VerifyOTPResponseSchema),
    },
)
async def verify_email(request, payload: VerifyOTPSchema):
    request.logger.info("[1] Entering verify_email endpoint")
    user = await User.objects.filter(email=payload.email).afirst()
    if not user:
        request.logger.warning(f"[2] User not found for email: {payload.email}")
        request.logger.info("[3] Exiting verify_email endpoint with error")
        return 400, {"error": {"message": "Invalid request"}, "trace_id": str(request.trace_id), "data": None}

    request.logger.info(f"[2] Verifying OTP for user: {user.id}")
    ok = await UserService.verify_otp(
        user=user,
        code=payload.code,
        purpose="verify_email",
    )
    if not ok:
        request.logger.warning("[3] OTP verification failed or expired")
        request.logger.info("[4] Exiting verify_email endpoint with error")
        return 400, {
            "error": {"message": "Invalid or expired OTP"},
            "trace_id": str(request.trace_id),
            "data": None,
        }

    request.logger.info("[3] OTP verified successfully")
    request.logger.info("[4] Exiting verify_email endpoint")
    return 200, {"data": {"verified": True}, "trace_id": str(request.trace_id), "error": {}}


@router.post(
    "/password-reset/request",
    response={
        200: create_api_response_schema(ResetPasswordRequestResponseSchema),
        400: create_api_response_schema(ResetPasswordRequestResponseSchema),
    },
)
async def reset_password_request(request, payload: ResetPasswordRequestSchema):
    request.logger.info("[1] Entering reset_password_request endpoint")
    request.logger.info(f"[2] Initiating password reset for email: {payload.email}")
    await UserService.initiate_password_reset(payload.email)
    request.logger.info("[3] Exiting reset_password_request endpoint")
    return 200, {"data": {"status": "ok"}, "trace_id": str(request.trace_id), "error": {}}


@router.post(
    "/password-reset/confirm",
    response={
        200: create_api_response_schema(ResetPasswordConfirmResponseSchema),
        400: create_api_response_schema(ResetPasswordConfirmResponseSchema),
    },
)
async def reset_password_confirm(request, payload: ResetPasswordConfirmSchema):
    request.logger.info("[1] Entering reset_password_confirm endpoint")
    user = await User.objects.filter(email=payload.email).afirst()
    if not user:
        request.logger.warning(f"[2] User not found for email: {payload.email}")
        request.logger.info("[3] Exiting reset_password_confirm endpoint with error")
        return 400, {"error": {"message": "Invalid request"}, "trace_id": str(request.trace_id), "data": None}

    request.logger.info(f"[2] Resetting password for user: {user.id}")
    ok = await UserService.reset_password(
        user=user,
        code=payload.code,
        new_password=payload.new_password,
    )
    if not ok:
        request.logger.warning("[3] Password reset failed: Invalid or expired OTP")
        request.logger.info("[4] Exiting reset_password_confirm endpoint with error")
        return 400, {
            "error": {"message": "Invalid or expired OTP"},
            "trace_id": str(request.trace_id),
            "data": None,
        }

    request.logger.info("[3] Password reset successful")
    request.logger.info("[4] Exiting reset_password_confirm endpoint")
    return 200, {"data": {"password_reset": True}, "trace_id": str(request.trace_id), "error": {}}
