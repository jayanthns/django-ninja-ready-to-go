from typing import Any, Dict, List

from ninja import Router

from common.base_schemas import create_api_response_schema

from .schemas import AnimalCreateSchema, AnimalSchema
from .services import AnimalService

router = Router()


# @router.post("/", response=APIResponseSchema[AnimalSchema])
@router.post("/", response=create_api_response_schema(AnimalSchema))
async def create_animal(request, payload: AnimalCreateSchema):
    """Create a new animal (Async)."""
    return {
        "data": await AnimalService.create_animal(payload.name, payload.species, payload.age),
        "trace_id": str(request.trace_id),
        "error": {},
    }


# @router.get("/", response=APIResponseSchema[List[AnimalSchema]])
@router.get("/", response=create_api_response_schema(List[AnimalSchema]))
async def list_animals(request):
    """Retrieve all animals (Async)."""
    return {"data": await AnimalService.list_animals(), "trace_id": str(request.trace_id), "error": {}}


# @router.get("/{animal_id}/", response={200: APIResponseSchema[AnimalSchema], 404: APIResponseSchema[Dict[str, Any]]})
@router.get("/{animal_id}/", response={200: AnimalSchema, 404: Dict[str, Any]})
async def get_animal(request, animal_id: int):
    """Retrieve a single animal by ID (Async)."""
    animal = await AnimalService.get_animal(animal_id)
    if not animal:
        return 404, {"error": "Animal not found"}
    return animal


# @router.put("/{animal_id}/", response={200: APIResponseSchema[AnimalSchema], 404: APIResponseSchema[Dict[str, Any]]})
@router.put("/{animal_id}/", response={200: AnimalSchema, 404: Dict[str, Any]})
async def update_animal(request, animal_id: int, payload: AnimalCreateSchema):
    """Update an animal (Async)."""
    animal = await AnimalService.update_animal(animal_id, payload)
    if not animal:
        return 404, {"error": "Animal not found"}
    return animal


# @router.delete("/{animal_id}/", response={200: APIResponseSchema[Dict[str, str]], 404: APIResponseSchema[Dict[str, str]]})
@router.delete("/{animal_id}/", response={200: Dict[str, str], 404: Dict[str, str]})
async def delete_animal(request, animal_id: int):
    """Delete an animal (Async)."""
    success = await AnimalService.delete_animal(animal_id)
    if not success:
        return 404, {"error": "Animal not found"}
    return {"message": "Animal deleted successfully"}
