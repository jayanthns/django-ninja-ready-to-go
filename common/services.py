from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from django.db import models
from pydantic import BaseModel

T = TypeVar("T", bound=models.Model)


class BaseCRUDService:
    model: Type[T]

    @classmethod
    async def create(cls, data: Union[BaseModel, Dict[str, Any]]) -> T:
        """
        Create a new instance asynchronously.
        Accepts a Pydantic Schema or a dictionary.
        """
        if isinstance(data, BaseModel):
            data = data.dict(exclude_unset=True)
        return await cls.model.objects.acreate(**data)

    @classmethod
    async def list(cls) -> List[T]:
        """
        Retrieve all instances asynchronously.
        """
        return [item async for item in cls.model.objects.all()]

    @classmethod
    async def get(cls, id: Any) -> Optional[T]:
        """
        Retrieve a single instance by ID asynchronously.
        """
        return await cls.model.objects.filter(pk=id).afirst()

    @classmethod
    async def update(cls, id: Any, data: Union[BaseModel, Dict[str, Any]]) -> Optional[T]:
        """
        Update an instance asynchronously.
        Fetches, updates fields, and calls asave() to ensure audits trigger.
        """
        try:
            instance = await cls.model.objects.aget(pk=id)
        except cls.model.DoesNotExist:
            return None

        if isinstance(data, BaseModel):
            data = data.dict(exclude_unset=True)

        for field, value in data.items():
            setattr(instance, field, value)

        await instance.asave()
        return instance

    @classmethod
    async def delete(cls, id: Any) -> bool:
        """
        Delete an instance asynchronously.
        """
        count, _ = await cls.model.objects.filter(pk=id).adelete()
        return count > 0
