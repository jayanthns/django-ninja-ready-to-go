import time
from typing import Optional, Tuple

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache

from ..schemas import RedisHealthSchema


class CacheHealthService:
    """Service for checking cache health (works with Redis or local memory)."""

    @staticmethod
    async def check_cache_health() -> RedisHealthSchema:
        """
        Perform cache health check (Redis or LocMem backend).
        """
        start_time = time.time()
        error_message = None
        backend_type = getattr(settings, "USE_REDIS", False)
        redis_health_info = {
            "is_healthy": False,
            "response_time_ms": 0,
            "error_message": None,
            "redis_version": None,
            "memory_usage": None,
            "connected_clients": None,
            "uptime_in_seconds": None,
            "total_commands_processed": None,
            "evicted_keys": None,
            "keyspace_hits": None,
            "keyspace_misses": None,
            "role": None,
        }
        try:
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"

            # Test write
            await cache.aset(test_key, test_value, timeout=10)
            # Test read
            retrieved_value = await cache.aget(test_key)

            if retrieved_value != test_value:
                error_message = "Cache read/write test failed - value mismatch"
            else:
                await cache.adelete(test_key)

                # Only try Redis info if backend is Redis
                if backend_type:
                    try:
                        client = CacheHealthService._get_redis_client()
                        if client:
                            info = await sync_to_async(client.info)()
                            redis_health_info = {
                                "redis_version": info.get("redis_version"),
                                "memory_usage": info.get("used_memory_human"),
                                "connected_clients": info.get("connected_clients"),
                                "uptime_in_seconds": info.get("uptime_in_seconds"),
                                "total_commands_processed": info.get("total_commands_processed"),
                                "evicted_keys": info.get("evicted_keys"),
                                "keyspace_hits": info.get("keyspace_hits"),
                                "keyspace_misses": info.get("keyspace_misses"),
                                "role": info.get("role"),
                            }
                    except Exception as e:
                        print(f"Error getting Redis info: {e}")
                        # skip info retrieval if not redis or unsupported
                        error_message = f"Failed to retrieve Redis info: {str(e)}"

        except Exception as e:
            error_message = f"Cache connection failed: {str(e)}"

        response_time_ms = round((time.time() - start_time) * 1000, 2)
        is_healthy = error_message is None
        redis_health_info.update(
            {
                "response_time_ms": response_time_ms,
                "error_message": error_message,
                "is_healthy": is_healthy,
            }
        )

        return RedisHealthSchema(**redis_health_info)

    @staticmethod
    def _get_redis_client():
        """Return raw redis connection if backend is Redis."""
        try:
            client_wrapper = cache.client.get_client(write=True)
            if hasattr(client_wrapper, "client") and hasattr(client_wrapper.client, "get_connection"):
                return client_wrapper.client.get_connection("write")
            if hasattr(client_wrapper, "get_connection"):
                return client_wrapper.get_connection("write")
            return client_wrapper
        except Exception as e:
            print(f"Error getting Redis connection: {e}")
            return None

    @staticmethod
    async def test_cache_write() -> Tuple[bool, Optional[str]]:
        """Verify cache write/read/delete operations."""
        try:
            test_key = f"write_test_{int(time.time())}"
            test_value = "test_value"

            await cache.aset(test_key, test_value, timeout=60)
            retrieved_value = await cache.aget(test_key)

            if retrieved_value != test_value:
                return False, "Cache write test failed - value mismatch"

            await cache.adelete(test_key)
            return True, None
        except Exception as e:
            return False, f"Cache write test failed: {str(e)}"

    @staticmethod
    async def test_cache_read() -> Tuple[bool, Optional[str]]:
        """Verify cache read operation."""
        try:
            result = await sync_to_async(cache.get)("non_existent_key")
            _ = result
            return True, None
        except Exception as e:
            return False, f"Cache read test failed: {str(e)}"
