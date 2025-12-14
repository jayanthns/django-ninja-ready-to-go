import uuid
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
@router.get("/{animal_id}/", response={200: AnimalSchema, 404: Dict[str, Any]})
async def get_animal(request, animal_id: uuid.UUID):
    """Retrieve a single animal by ID (Async)."""
    request.logger.info(f"[1] Entering get_animal endpoint for ID: {animal_id}")
    animal = await AnimalService.get(animal_id)
    if not animal:
        request.logger.warning(f"[2] Animal not found: {animal_id}")
        request.logger.info("[3] Exiting get_animal endpoint (Not Found)")
        return 404, {"error": "Animal not found"}
    request.logger.info("[2] Found animal")
    request.logger.info("[3] Exiting get_animal endpoint")
    return animal


# @router.put("/{animal_id}/", response={200: APIResponseSchema[AnimalSchema], 404: APIResponseSchema[Dict[str, Any]]})
@router.put("/{animal_id}/", response={200: AnimalSchema, 404: Dict[str, Any]})
async def update_animal(request, animal_id: uuid.UUID, payload: AnimalCreateSchema):
    """Update an animal (Async)."""
    request.logger.info(f"[1] Entering update_animal endpoint for ID: {animal_id}")
    animal = await AnimalService.update(animal_id, payload)
    if not animal:
        request.logger.warning(f"[2] Animal not found for update: {animal_id}")
        request.logger.info("[3] Exiting update_animal endpoint (Not Found)")
        return 404, {"error": "Animal not found"}
    request.logger.info("[2] Successfully updated animal")
    request.logger.info("[3] Exiting update_animal endpoint")
    return animal


# @router.delete("/{animal_id}/", response={200: APIResponseSchema[Dict[str, str]], 404: APIResponseSchema[Dict[str, str]]}) # noqa: E501
@router.delete("/{animal_id}/", response={200: Dict[str, str], 404: Dict[str, str]})
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
            return 404, {"error": "Animal not found"}

        # Log successful deletion
        request.logger.info(f"[4] Successfully deleted animal with ID: {animal_id}")
        request.logger.info("[5] Exiting delete_animal endpoint")
        return {"message": "Animal deleted successfully"}

    except Exception as e:
        # Log the error
        request.logger.exception(f"[Error] Failed to delete animal: {animal_id} with error: {str(e)}")
        raise


@router.get("/logger-demo/", response=Dict[str, Any])
async def logger_demo(request):
    """Demo endpoint to showcase the logger helper functionality."""
    # Use request.logger directly
    request.logger.debug("[1] This is a debug message - usually not shown in production")
    request.logger.info("[2] This is an info message - normal operation flow")
    request.logger.warning("[3] This is a warning message - something unusual but not critical")

    # Demonstrate updating context
    request.logger.update_context(demo_step="context_update", custom_field="custom_value")

    request.logger.info("[4] This message includes updated context")

    # Demonstrate error logging (without actually raising)
    try:
        # Simulate some operation
        result = 42 / 1  # This will succeed
        request.logger.info(f"[5] Operation completed successfully: {result}")
    except Exception as e:
        request.logger.exception(f"[Error] This would log an exception with full traceback: {str(e)}")

    # Get current context
    current_context = request.logger.get_context()

    return {
        "message": "Logger helper demo completed successfully!",
        "trace_id": str(request.trace_id),
        "correlation_id": getattr(request, "correlation_id", None),
        "current_context": current_context,
        "request_info": {
            "method": request.method,
            "path": request.path,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        },
    }
