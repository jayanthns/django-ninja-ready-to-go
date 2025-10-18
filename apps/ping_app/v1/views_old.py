# """
# Main ping app router - combines cache, database, and external health checks.
# """

# from typing import Any, Dict

# from ninja import Router

# from common.base_schemas import create_api_response_schema

# from .cache_views import router as cache_router
# from .database_views import router as database_router
# from .external_views import router as external_router
# from .schemas import SystemStatusSchema
# from .services import SystemHealthService

# router = Router()

# # Include sub-routers
# router.add_router("/cache", cache_router, tags=["cache-health"])
# router.add_router("/db", database_router, tags=["database-health"])
# router.add_router("/external", external_router, tags=["external-pings"])


# @router.get("/", response=create_api_response_schema(Dict[str, str]))
# async def ping(request):
#     """Basic ping endpoint to test API connectivity."""
#     request.logger.info("Basic ping endpoint accessed")

#     return {
#         "data": {"message": "pong", "status": "healthy"},
#         "trace_id": str(request.trace_id),
#         "error": {},
#     }


# @router.get("/health/", response=create_api_response_schema(SystemStatusSchema))
# async def get_system_health(request):
#     """Get overall system health status."""
#     request.logger.info("Performing system health check")

#     try:
#         health_status = await SystemHealthService.check_system_health()

#         # Log the health check
#         for service in health_status.services:
#             await SystemHealthService.log_health_check(
#                 service_name=service.service_name,
#                 service_type=service.service_type,
#                 is_healthy=service.is_healthy,
#                 response_time_ms=service.response_time_ms,
#                 error_message=service.error_message,
#                 metadata=service.metadata,
#             )

#         request.logger.info(f"System health check completed - Status: {health_status.overall_status}")

#         return {
#             "data": health_status,
#             "trace_id": str(request.trace_id),
#             "error": {},
#         }

#     except Exception as e:
#         request.logger.exception("Error performing system health check")
#         raise
