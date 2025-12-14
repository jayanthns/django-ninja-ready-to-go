import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.animals_app.v1.views import create_animal, delete_animal, get_animal, update_animal


@pytest.fixture
def mock_request():
    mock = MagicMock()
    mock.trace_id = uuid.uuid4()
    mock.logger = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_create_animal(mock_request):
    with patch("apps.animals_app.v1.services.AnimalService.create", new_callable=AsyncMock) as mock_create:
        mock_id = uuid.uuid4()
        mock_create.return_value = AsyncMock(id=mock_id, name="TestDog", species="Dog", age=3)
        mock_create.return_value.id = mock_id
        mock_create.return_value.name = "TestDog"
        mock_create.return_value.species = "Dog"
        mock_create.return_value.age = 3

        payload = MagicMock()
        payload.name = "TestDog"
        payload.species = "Dog"
        payload.age = 3

        response = await create_animal(mock_request, payload)

        # View returns a dict directly
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["error"] == {}
        assert response["data"] is not None
        # Verify call
        mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_animal(mock_request):
    mock_id = uuid.uuid4()

    with patch("apps.animals_app.v1.services.AnimalService.get", new_callable=AsyncMock) as mock_get:
        # Mock success
        mock_get.return_value = AsyncMock(id=mock_id, name="TestDog", species="Dog", age=3)
        mock_get.return_value.id = mock_id

        status, response = await get_animal(mock_request, mock_id)

        assert status == 200
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["error"] == {}
        assert response["data"] is not None


@pytest.mark.asyncio
async def test_get_animal_not_found(mock_request):
    mock_id = uuid.uuid4()

    with patch("apps.animals_app.v1.services.AnimalService.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        status, response = await get_animal(mock_request, mock_id)

        assert status == 404
        assert response["error"]["message"] == "Animal not found"
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["data"] is None


@pytest.mark.asyncio
async def test_update_animal(mock_request):
    mock_id = uuid.uuid4()

    with patch("apps.animals_app.v1.services.AnimalService.update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = AsyncMock(id=mock_id, name="UpdatedDog", species="Dog", age=4)
        mock_update.return_value.id = mock_id

        payload = MagicMock()

        status, response = await update_animal(mock_request, mock_id, payload)

        assert status == 200
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["error"] == {}
        assert response["data"] is not None


@pytest.mark.asyncio
async def test_delete_animal(mock_request):
    mock_id = uuid.uuid4()

    with patch("apps.animals_app.v1.services.AnimalService.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = True

        status, response = await delete_animal(mock_request, mock_id)

        assert status == 200
        assert response["data"]["message"] == "Animal deleted successfully"
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["error"] == {}


@pytest.mark.asyncio
async def test_delete_animal_not_found(mock_request):
    mock_id = uuid.uuid4()

    with patch("apps.animals_app.v1.services.AnimalService.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = False

        status, response = await delete_animal(mock_request, mock_id)

        assert status == 404
        assert response["error"]["message"] == "Animal not found"
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["data"] is None


@pytest.mark.asyncio
async def test_list_animals(mock_request):
    with patch("apps.animals_app.v1.services.AnimalService.list", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            AsyncMock(id=uuid.uuid4(), name="Dog1", species="Dog", age=2),
            AsyncMock(id=uuid.uuid4(), name="Cat1", species="Cat", age=5),
        ]
        mock_list.return_value[0].id = uuid.uuid4()
        mock_list.return_value[0].name = "Dog1"
        mock_list.return_value[0].species = "Dog"
        mock_list.return_value[0].age = 2

        from apps.animals_app.v1.views import list_animals

        response = await list_animals(mock_request)

        assert response["trace_id"] == str(mock_request.trace_id)
        assert len(response["data"]) == 2


@pytest.mark.asyncio
async def test_update_animal_not_found(mock_request):
    mock_id = uuid.uuid4()

    with patch("apps.animals_app.v1.services.AnimalService.update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = None

        payload = MagicMock()

        status, response = await update_animal(mock_request, mock_id, payload)

        assert status == 404
        assert response["error"]["message"] == "Animal not found"
        assert response["trace_id"] == str(mock_request.trace_id)
        assert response["data"] is None


@pytest.mark.asyncio
async def test_create_animal_exception(mock_request):
    with patch("apps.animals_app.v1.services.AnimalService.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("Crash")

        payload = MagicMock()
        payload.name = "CrashDog"

        with pytest.raises(Exception):
            await create_animal(mock_request, payload)

        mock_request.logger.exception.assert_called_once()


@pytest.mark.asyncio
async def test_delete_animal_exception(mock_request):
    mock_id = uuid.uuid4()
    with patch("apps.animals_app.v1.services.AnimalService.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.side_effect = Exception("Delete failed")

        with pytest.raises(Exception):
            await delete_animal(mock_request, mock_id)

        mock_request.logger.exception.assert_called_once()
