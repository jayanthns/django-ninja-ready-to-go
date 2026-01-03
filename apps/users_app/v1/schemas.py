import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSchema(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=32)


class ExtraUserCreateSchema(BaseModel):
    is_verified: bool = False


class UserCreateResponseSchema(UserSchema, ExtraUserCreateSchema):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class VerifyOTPSchema(BaseModel):
    email: EmailStr
    code: str


class VerifyOTPResponseSchema(BaseModel):
    verified: bool


class ResetPasswordRequestSchema(BaseModel):
    email: EmailStr


class ResetPasswordRequestResponseSchema(BaseModel):
    status: str


class ResetPasswordConfirmSchema(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class ResetPasswordConfirmResponseSchema(BaseModel):
    password_reset: bool
