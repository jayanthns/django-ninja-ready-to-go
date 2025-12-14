from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from common.services import BaseCRUDService


# Dummy Schema
class DummySchema(BaseModel):
    field1: str


# Dummy Model Service
class DummyService(BaseCRUDService):
    model = MagicMock()


@pytest.mark.asyncio
class TestBaseCRUDService:
    async def test_create_with_schema(self):
        schema = DummySchema(field1="value")
        DummyService.model.objects.acreate = AsyncMock(return_value="created_instance")

        # Hooks are no-op by default, but we should verify the whole flow works
        result = await DummyService.create(schema)

        assert result == "created_instance"
        DummyService.model.objects.acreate.assert_awaited_with(field1="value")

    async def test_create_with_dict(self):
        data = {"field1": "value"}
        DummyService.model.objects.acreate = AsyncMock(return_value="created_instance")

        result = await DummyService.create(data)

        assert result == "created_instance"
        DummyService.model.objects.acreate.assert_awaited_with(field1="value")

    async def test_list(self):
        # Mocking async iterator
        mock_qs = MagicMock()
        mock_qs.__aiter__.return_value = iter(["item1", "item2"])
        DummyService.model.objects.all.return_value = mock_qs

        result = await DummyService.list()

        assert result == ["item1", "item2"]
        DummyService.model.objects.all.assert_called_once()

    async def test_get(self):
        DummyService.model.objects.filter.return_value.afirst = AsyncMock(return_value="instance")

        result = await DummyService.get(1)

        assert result == "instance"
        DummyService.model.objects.filter.assert_called_with(pk=1)

    async def test_update_success(self):
        mock_instance = MagicMock()
        mock_instance.asave = AsyncMock()
        DummyService.model.objects.aget = AsyncMock(return_value=mock_instance)

        data = {"field1": "new_value"}
        result = await DummyService.update(1, data)

        assert result == mock_instance
        assert mock_instance.field1 == "new_value"
        mock_instance.asave.assert_awaited_once()

    async def test_update_schema(self):
        mock_instance = MagicMock()
        mock_instance.asave = AsyncMock()
        DummyService.model.objects.aget = AsyncMock(return_value=mock_instance)

        schema = DummySchema(field1="new_value")
        result = await DummyService.update(1, schema)

        assert result == mock_instance
        assert mock_instance.field1 == "new_value"
        mock_instance.asave.assert_awaited_once()

    async def test_update_not_found(self):
        DummyService.model.DoesNotExist = Exception  # Mock the exception class
        DummyService.model.objects.aget = AsyncMock(side_effect=DummyService.model.DoesNotExist)

        result = await DummyService.update(1, {})

        assert result is None

    async def test_delete(self):
        # New implementation uses aget + instance.adelete
        mock_instance = MagicMock()
        mock_instance.adelete = AsyncMock()
        DummyService.model.objects.aget = AsyncMock(return_value=mock_instance)

        result = await DummyService.delete(1)

        assert result is True
        DummyService.model.objects.aget.assert_awaited_with(pk=1)
        mock_instance.adelete.assert_awaited_once()

    async def test_delete_fail(self):
        DummyService.model.DoesNotExist = Exception
        DummyService.model.objects.aget = AsyncMock(side_effect=DummyService.model.DoesNotExist)

        result = await DummyService.delete(1)

        assert result is False
