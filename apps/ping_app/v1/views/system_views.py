"""
System health check endpoints.
"""

from typing import Dict

from ninja import Router

from common.base_schemas import create_api_response_schema

from ..schemas import SystemStatusSchema
from ..services import SystemHealthService

router = Router()


@router.get("/", response=create_api_response_schema(Dict[str, str]))
async def ping(request):
    """Basic ping endpoint to test API connectivity."""
    request.logger.info("[1] Entering ping endpoint")

    response_data = {"message": "pong", "status": "healthy"}

    request.logger.info("[2] Exiting ping endpoint")
    return {
        "data": response_data,
        "trace_id": str(request.trace_id),
        "error": {},
    }


@router.get("/health/", response=create_api_response_schema(SystemStatusSchema))
async def get_system_health(request):
    """Get overall system health status."""
    request.logger.info("[1] Entering get_system_health endpoint")

    try:
        request.logger.info("[2] Calling SystemHealthService.check_system_health")
        health_status = await SystemHealthService.check_system_health()

        request.logger.info("[3] Logging health checks for services")
        for service in health_status.services:
            await SystemHealthService.log_health_check(
                service_name=service.service_name,
                service_type=service.service_type,
                is_healthy=service.is_healthy,
                response_time_ms=service.response_time_ms,
                error_message=service.error_message,
                metadata=service.metadata,
            )

        request.logger.info(f"[4] System health check completed - Status: {health_status.overall_status}")

        request.logger.info("[5] Exiting get_system_health endpoint")
        return {
            "data": health_status,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception(f"[Error] Error performing system health check: {e}")
        request.logger.info(f"[Exit-Error] Exiting get_system_health endpoint with error: {e}")

        return {
            "data": {},
            "trace_id": str(request.trace_id),
            "error": {
                "message": "System health check failed",
                "details": str(e),
            },
        }
