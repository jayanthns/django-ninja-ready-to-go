import os

# ------------------------------------------------------------------------------
# 🔧 Cache configuration switch
# ------------------------------------------------------------------------------

USE_REDIS = os.getenv("USE_REDIS", "0") == "1"

REDIS_HOST_AND_PORT = os.getenv("REDIS_HOST_AND_PORT", "localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

if USE_REDIS:
    # ------------------------------------------------------------------------------
    # ✅ Redis cache configuration (using django-redis)
    # ------------------------------------------------------------------------------
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://redis:{REDIS_PASSWORD}@{REDIS_HOST_AND_PORT}/0",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 2,  # seconds
                "SOCKET_TIMEOUT": 2,  # seconds
                "CONNECTION_POOL_KWARGS": {"max_connections": 100},
                # "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            },
            "KEY_PREFIX": "myapp",  # optional namespace
            "TIMEOUT": 60 * 5,  # default 5 min cache TTL
        }
    }

    CACHE_BACKEND_NAME = "Redis"
else:
    # ------------------------------------------------------------------------------
    # 💾 Local in-memory cache (for dev / fallback)
    # ------------------------------------------------------------------------------
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",  # required unique key
        }
    }

    CACHE_BACKEND_NAME = "InMemory"
