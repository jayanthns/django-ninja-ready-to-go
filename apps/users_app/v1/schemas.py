import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSchema(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
