from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True  # ✅ Allows async model conversion


class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
