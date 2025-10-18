"""
External endpoint pinging and monitoring endpoints.
"""

from typing import Any, Dict, List

from ninja import Router

from common.base_schemas import create_api_response_schema

from ..schemas import PingRequestSchema, PingResponseSchema, PingStatsSchema
from ..services import PingService

router = Router()


@router.get("/", response=create_api_response_schema(Dict[str, str]))
async def ping_external(request):
    """Basic ping endpoint to test external ping service connectivity."""
    request.logger.info("Basic external ping endpoint accessed")

    return {
        "data": {"message": "external ping service ready", "status": "healthy"},
        "trace_id": str(request.trace_id),
        "error": {},
    }


@router.post("/endpoint/", response=create_api_response_schema(PingResponseSchema))
async def ping_endpoint(request, payload: PingRequestSchema):
    """Ping an external endpoint and log the result."""
    request.logger.info(f"Pinging endpoint: {payload.endpoint} with method: {payload.method}")

    try:
        # Perform the ping
        ping_response = await PingService.ping_endpoint(payload)

        # Log the result to database
        await PingService.log_ping_result(payload, ping_response)

        # Log the operation
        if ping_response.success:
            request.logger.info(
                f"Successfully pinged {payload.endpoint} - Status: {ping_response.status_code}, Time: {ping_response.response_time_ms:.2f}ms"
            )
        else:
            request.logger.warning(
                f"Failed to ping {payload.endpoint} - Status: {ping_response.status_code}, Error: {ping_response.error_message}"
            )

        return {
            "data": ping_response,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception(f"Error pinging endpoint {payload.endpoint}: {e}")
        raise


@router.get("/logs/", response=create_api_response_schema(List[PingResponseSchema]))
async def get_ping_logs(request, limit: int = 100):
    """Get recent ping logs."""
    request.logger.info(f"Retrieving ping logs with limit: {limit}")

    try:
        logs = await PingService.get_ping_logs(limit)
        request.logger.info(f"Retrieved {len(logs)} ping logs")

        return {
            "data": logs,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception(f"Error retrieving ping logs: {e}")
        raise


@router.get("/stats/", response=create_api_response_schema(PingStatsSchema))
async def get_ping_stats(request):
    """Get ping statistics."""
    request.logger.info("Retrieving ping statistics")

    try:
        stats = await PingService.get_ping_stats()
        request.logger.info(
            f"Retrieved ping stats - Total: {stats.total_pings}, Success Rate: {stats.last_24h_success_rate:.2f}%"
        )

        return {
            "data": stats,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception(f"Error retrieving ping statistics: {e}")
        raise


@router.get("/health/", response=create_api_response_schema(Dict[str, Any]))
async def get_external_ping_health(request):
    """Get external ping service health status."""
    request.logger.info("Getting external ping service health")

    try:
        # Get recent ping statistics
        stats = await PingService.get_ping_stats()

        # Determine health based on recent success rate
        health_status = "healthy"
        if stats.last_24h_success_rate < 80:
            health_status = "degraded"
        if stats.last_24h_success_rate < 50:
            health_status = "unhealthy"

        health_info = {
            "service_name": "External Ping Service",
            "status": health_status,
            "last_24h_stats": {
                "total_pings": stats.last_24h_pings,
                "successful_pings": stats.last_24h_successful,
                "success_rate": stats.last_24h_success_rate,
            },
            "overall_stats": {
                "total_pings": stats.total_pings,
                "successful_pings": stats.successful_pings,
                "failed_pings": stats.failed_pings,
                "average_response_time_ms": stats.average_response_time_ms,
            },
        }

        request.logger.info(f"External ping service health: {health_status}")

        return {
            "data": health_info,
            "trace_id": str(request.trace_id),
            "error": {},
        }

    except Exception as e:
        request.logger.exception(f"Error getting external ping service health: {e}")
        raise
