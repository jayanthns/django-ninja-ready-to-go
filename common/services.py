from abc import ABC
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from django.db import models
from pydantic import BaseModel

T = TypeVar("T", bound=models.Model)


class BaseCRUDService(ABC):
    """
    Abstract base CRUD service.

    Rules:
    - Subclasses MUST define `model`
    - All writes go through instance save/asave (audit-safe)
    - QuerySet.update / aupdate is never used
    """

    model: Type[T]

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    @classmethod
    def _normalize_data(cls, data: Union[BaseModel, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(data, BaseModel):
            return data.dict(exclude_unset=True)
        return data

    # ---------------------------------------------------------
    # Hooks (override in subclasses if needed)
    # ---------------------------------------------------------

    @classmethod
    async def before_create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @classmethod
    async def after_create(cls, instance: T) -> None:
        pass

    @classmethod
    async def before_update(cls, instance: T, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    @classmethod
    async def after_update(cls, instance: T) -> None:
        pass

    @classmethod
    async def after_delete(cls, instance: T) -> None:
        pass

    # ---------------------------------------------------------
    # CRUD operations
    # ---------------------------------------------------------

    @classmethod
    async def create(cls, data: Union[BaseModel, Dict[str, Any]]) -> T:
        payload = cls._normalize_data(data)
        payload = await cls.before_create(payload)

        instance = await cls.model.objects.acreate(**payload)

        await cls.after_create(instance)
        return instance

    @classmethod
    async def list(cls) -> List[T]:
        return [obj async for obj in cls.model.objects.all()]

    @classmethod
    async def get(cls, id: Any) -> Optional[T]:
        return await cls.model.objects.filter(pk=id).afirst()

    @classmethod
    async def update(cls, id: Any, data: Union[BaseModel, Dict[str, Any]]) -> Optional[T]:
        try:
            instance = await cls.model.objects.aget(pk=id)
        except cls.model.DoesNotExist:
            return None

        payload = cls._normalize_data(data)
        payload = await cls.before_update(instance, payload)

        for field, value in payload.items():
            setattr(instance, field, value)

        # IMPORTANT: instance-level save (audit-safe)
        await instance.asave()

        await cls.after_update(instance)
        return instance

    @classmethod
    async def delete(cls, id: Any) -> bool:
        try:
            instance = await cls.model.objects.aget(pk=id)
        except cls.model.DoesNotExist:
            return False

        await instance.adelete()
        await cls.after_delete(instance)
        return True
