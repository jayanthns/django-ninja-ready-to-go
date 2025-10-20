"""
Cache health check endpoints for Redis connectivity and operations.
"""

from typing import Any, Dict

from ninja import Router
from ninja.responses import Response

# from apps.ping_app.v1.services import CacheHealthService, SystemHealthService
from common.base_schemas import create_api_response_schema

from ..schemas import RedisHealthSchema
from ..services import CacheHealthService, SystemHealthService

router = Router()


@router.get("/", response=create_api_response_schema(RedisHealthSchema))
async def ping_cache(request):
    """
    Ping cache service to check connectivity.

    Returns:
        Cache connection status and response time
    """
    request.logger.info("Pinging cache service")

    try:
        # Check basic connectivity
        redis_health = await CacheHealthService.check_cache_health()

        # Test read permissions
        read_success, read_error = await CacheHealthService.test_cache_read()
        if not read_success:
            redis_health.error_message = (
                f"{redis_health.error_message or ''} Read test failed: {read_error}".strip()
            )
            redis_health.is_healthy = False

        # Test write permissions
        write_success, write_error = await CacheHealthService.test_cache_write()
        if not write_success:
            redis_health.error_message = (
                f"{redis_health.error_message or ''} Write test failed: {write_error}".strip()
            )
            redis_health.is_healthy = False

        # Log the health check
        await SystemHealthService.log_health_check(
            service_name="Redis",
            service_type="redis",
            is_healthy=redis_health.is_healthy,
            response_time_ms=redis_health.response_time_ms,
            error_message=redis_health.error_message,
            metadata={
                "redis_version": redis_health.redis_version,
                "memory_usage": redis_health.memory_usage,
                "connected_clients": redis_health.connected_clients,
            },
        )

        if redis_health.is_healthy:
            request.logger.info(
                f"Cache ping successful - Response time: {redis_health.response_time_ms:.2f}ms"
            )
        else:
            request.logger.warning(f"Cache ping failed - {redis_health.error_message}")

        return Response(
            {
                "data": redis_health,
                "trace_id": str(request.trace_id),
                "error": {},
            },
            status=200,
        )

    except Exception as e:
        request.logger.exception(f"Error pinging cache service: {e}")

        return Response(
            {
                "data": {},
                "trace_id": str(request.trace_id),
                "error": {
                    "message": "Cache ping failed",
                    "details": str(e),
                },
            },
            status=400,
        )


@router.get("/info", response=create_api_response_schema(Dict[str, Any]))
async def get_cache_info(request):
    """
    Get cache service information and statistics.

    Returns:
        Cache service info, memory usage, and connection details
    """
    request.logger.info("Getting cache service information")

    try:
        # Check basic connectivity first
        redis_health = await CacheHealthService.check_cache_health()

        if not redis_health.is_healthy:
            raise Exception("Cache service is not responding")

        # Prepare detailed cache info
        cache_info = {
            "cache_type": "Redis",
            "is_healthy": redis_health.is_healthy,
            "response_time_ms": redis_health.response_time_ms,
            "server": {
                "version": redis_health.redis_version or "unknown",
                "memory_usage": redis_health.memory_usage or "unknown",
                "connected_clients": redis_health.connected_clients or 0,
            },
            "status": "healthy" if redis_health.is_healthy else "unhealthy",
        }

        request.logger.info("Cache info retrieved successfully")

        return Response(
            {
                "data": cache_info,
                "trace_id": str(request.trace_id),
                "error": {},
            },
            status=200,
        )

    except Exception as e:
        request.logger.exception(f"Failed to get cache info: {e}")
        return Response(
            {
                "data": {},
                "trace_id": str(request.trace_id),
                "error": {
                    "message": "Failed to get cache info",
                    "details": str(e),
                },
            },
            status=400,
        )


@router.get("/keys", response=create_api_response_schema(Dict[str, Any]))
async def get_cache_keys(request, pattern: str = "*", limit: int = 100):
    """
    Get cache keys matching a pattern.

    Args:
        pattern: Key pattern to match (default: "*")
        limit: Maximum number of keys to return (default: 100)

    Returns:
        List of cache keys matching the pattern
    """
    request.logger.info(f"Getting cache keys with pattern: {pattern}, limit: {limit}")

    try:
        from asgiref.sync import sync_to_async
        from django.conf import settings
        from django.core.cache import cache

        # Basic read/write test
        test_key = "cache_keys_test"
        test_value = f"test_{int(request.timestamp) if hasattr(request, 'timestamp') else 123456}"
        await cache.aset(test_key, test_value, timeout=10)
        retrieved_value = await cache.aget(test_key)
        if retrieved_value != test_value:
            raise Exception("Cache read/write test failed")
        await cache.adelete(test_key)

        # Check backend type
        use_redis = getattr(settings, "USE_REDIS", False)

        if use_redis:
            # Redis backend: attempt key listing
            client = cache.client.get_client(write=True)
            redis_conn = (
                client.client.get_connection("write") if hasattr(client.client, "get_connection") else client
            )
            keys = await sync_to_async(redis_conn.keys)(pattern)
            keys = [k.decode() if isinstance(k, bytes) else k for k in keys]
            keys = keys[:limit]

            response_data = {
                "cache_type": "Redis",
                "pattern": pattern,
                "limit": limit,
                "keys": keys,
                "status": "healthy",
            }
        else:
            # Memory backend: no key listing support
            response_data = {
                "cache_type": "LocalMemoryCache",
                "pattern": pattern,
                "limit": limit,
                "message": "Local memory cache doesn't support key listing. Use Redis for key enumeration.",
                "status": "healthy",
            }

        request.logger.info("Cache keys request completed")
        return Response(
            {
                "data": response_data,
                "trace_id": str(request.trace_id),
                "error": {},
            }
        )

    except Exception as e:
        request.logger.exception(f"Failed to get cache keys: {e}")
        return Response(
            {
                "data": {},
                "trace_id": str(request.trace_id),
                "error": {
                    "message": "Failed to get cache keys",
                    "details": str(e),
                },
            },
            status=400,
        )


@router.post("/test-write/", response=create_api_response_schema(Dict[str, Any]))
async def test_cache_write(request):
    """Test cache write permissions specifically."""
    request.logger.info("Testing cache write permissions")

    try:
        success, error_message = await CacheHealthService.test_cache_write()

        result = {
            "success": success,
            "error_message": error_message,
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Cache write test passed")
        else:
            request.logger.warning(f"Cache write test failed - {error_message}")

        return Response(
            {
                "data": result,
                "trace_id": str(request.trace_id),
                "error": {},
            },
            status=200 if success else 400,
        )

    except Exception as e:
        request.logger.exception(f"Error testing cache write permissions: {e}")
        return Response(
            {
                "data": {},
                "trace_id": str(request.trace_id),
                "error": {
                    "message": "Error testing cache write permissions",
                    "details": str(e),
                },
            },
            status=400,
        )


@router.post("/test-read/", response=create_api_response_schema(Dict[str, Any]))
async def test_cache_read(request):
    """Test cache read permissions specifically."""
    request.logger.info("Testing cache read permissions")

    try:
        success, error_message = await CacheHealthService.test_cache_read()

        result = {
            "success": success,
            "error_message": error_message,
            "timestamp": str(request.trace_id),
        }

        if success:
            request.logger.info("Cache read test passed")
        else:
            request.logger.warning(f"Cache read test failed - {error_message}")

        return Response(
            {
                "data": result,
                "trace_id": str(request.trace_id),
                "error": {},
            }
        )

    except Exception as e:
        request.logger.exception(f"Error testing cache read permissions: {e}")
        return Response(
            {
                "data": {},
                "trace_id": str(request.trace_id),
                "error": {
                    "message": "Error testing cache read permissions",
                    "details": str(e),
                },
            },
            status=400,
        )
