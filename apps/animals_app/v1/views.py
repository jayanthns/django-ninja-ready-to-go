import uuid
from typing import List

from ninja import Router

from common.base_schemas import create_api_response_schema, MessageSchema

from .schemas import AnimalCreateSchema, AnimalSchema
from .services import AnimalService

router = Router()


# @router.post("/", response=APIResponseSchema[AnimalSchema])
@router.post("/", response=create_api_response_schema(AnimalSchema))
async def create_animal(request, payload: AnimalCreateSchema):
    """Create a new animal (Async)."""
    # Use request.logger directly (automatically includes trace_id and correlation_id)
    request.logger.info("[1] Entering create_animal endpoint")
    request.logger.info(f"[2] Creating new animal: {payload.name} ({payload.species})")

    try:
        # Create the animal
        request.logger.info("[3] Calling AnimalService.create")
        animal = await AnimalService.create(payload)

        # Log successful creation
        request.logger.info(f"[4] Successfully created animal with ID: {animal.id}")

        request.logger.info("[5] Exiting create_animal endpoint")
        return {
            "data": animal,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        # Log the error with automatic trace context
        request.logger.exception(f"[Error] Failed to create animal: {payload.name} with error: {str(e)}")
        raise


# @router.get("/", response=APIResponseSchema[List[AnimalSchema]])
@router.get("/", response=create_api_response_schema(List[AnimalSchema]))
async def list_animals(request):
    """Retrieve all animals (Async)."""
    request.logger.info("[1] Entering list_animals endpoint")
    result = await AnimalService.list()
    request.logger.info("[2] Exiting list_animals endpoint")
    return {"data": result, "trace_id": str(request.trace_id), "error": {}}


# @router.get("/{animal_id}/", response={200: APIResponseSchema[AnimalSchema], 404: APIResponseSchema[Dict[str, Any]]})
@router.get(
    "/{animal_id}/",
    response={200: create_api_response_schema(AnimalSchema), 404: create_api_response_schema(AnimalSchema)},
)
async def get_animal(request, animal_id: uuid.UUID):
    """Retrieve a single animal by ID (Async)."""
    request.logger.info(f"[1] Entering get_animal endpoint for ID: {animal_id}")
    animal = await AnimalService.get(animal_id)
    if not animal:
        request.logger.warning(f"[2] Animal not found: {animal_id}")
        request.logger.info("[3] Exiting get_animal endpoint (Not Found)")
        return 404, {
            "error": {"message": "Animal not found"},
            "trace_id": str(request.trace_id),
            "data": None,
        }
    request.logger.info("[2] Found animal")
    request.logger.info("[3] Exiting get_animal endpoint")
    return 200, {"data": animal, "trace_id": str(request.trace_id), "error": {}}


# @router.put("/{animal_id}/", response={200: APIResponseSchema[AnimalSchema], 404: APIResponseSchema[Dict[str, Any]]})
@router.put(
    "/{animal_id}/",
    response={200: create_api_response_schema(AnimalSchema), 404: create_api_response_schema(AnimalSchema)},
)
async def update_animal(request, animal_id: uuid.UUID, payload: AnimalCreateSchema):
    """Update an animal (Async)."""
    request.logger.info(f"[1] Entering update_animal endpoint for ID: {animal_id}")
    animal = await AnimalService.update(animal_id, payload)
    if not animal:
        request.logger.warning(f"[2] Animal not found for update: {animal_id}")
        request.logger.info("[3] Exiting update_animal endpoint (Not Found)")
        return 404, {
            "error": {"message": "Animal not found"},
            "trace_id": str(request.trace_id),
            "data": None,
        }
    request.logger.info("[2] Successfully updated animal")
    request.logger.info("[3] Exiting update_animal endpoint")
    return 200, {"data": animal, "trace_id": str(request.trace_id), "error": {}}


# @router.delete("/{animal_id}/", response={200: APIResponseSchema[Dict[str, str]], 404: APIResponseSchema[Dict[str, str]]}) # noqa: E501
@router.delete(
    "/{animal_id}/",
    response={200: create_api_response_schema(MessageSchema), 404: create_api_response_schema(MessageSchema)},
)
async def delete_animal(request, animal_id: uuid.UUID):
    """Delete an animal (Async)."""
    # Use request.logger directly
    request.logger.info("[1] Entering delete_animal endpoint")
    request.logger.info(f"[2] Attempting to delete animal with ID: {animal_id}")

    try:
        request.logger.info("[3] Calling AnimalService.delete")
        success = await AnimalService.delete(animal_id)
        if not success:
            request.logger.warning(f"[4] Animal not found for deletion: {animal_id}")
            request.logger.info("[5] Exiting delete_animal endpoint (Not Found)")
            return 404, {
                "error": {"message": "Animal not found"},
                "trace_id": str(request.trace_id),
                "data": None,
            }

        # Log successful deletion
        request.logger.info(f"[4] Successfully deleted animal with ID: {animal_id}")
        request.logger.info("[5] Exiting delete_animal endpoint")
        return 200, {
            "data": {"message": "Animal deleted successfully"},
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        # Log the error
        request.logger.exception(f"[Error] Failed to delete animal: {animal_id} with error: {str(e)}")
        raise
