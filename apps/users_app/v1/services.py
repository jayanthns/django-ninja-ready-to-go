from typing import Any, Dict, Union

from django.contrib.auth.hashers import make_password
from pydantic import BaseModel

from common.services import BaseCRUDService

from .models import User


class UserService(BaseCRUDService):
    model = User

    @classmethod
    async def create(cls, data: Union[BaseModel, Dict[str, Any]]) -> User:
        if isinstance(data, BaseModel):
            data = data.dict(exclude_unset=True)

        if "password" in data:
            data["password"] = make_password(data["password"])

        return await super().create(data)
