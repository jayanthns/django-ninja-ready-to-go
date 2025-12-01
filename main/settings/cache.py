import os

# ------------------------------------------------------------------------------
# 🔧 Cache configuration switch
# ------------------------------------------------------------------------------

USE_REDIS = os.getenv("USE_REDIS", "0") == "1"

REDIS_HOST_AND_PORT = os.getenv("REDIS_HOST_AND_PORT", "localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "")

if USE_REDIS:
    # ------------------------------------------------------------------------------
    # ✅ Redis cache configuration (using django-redis)
    # ------------------------------------------------------------------------------
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST_AND_PORT}/0",
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


# ------------------------------------------------------------------------------
# 🐇 Celery & Dramatiq Configuration
# ------------------------------------------------------------------------------

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")

if not CELERY_BROKER_URL and USE_REDIS:
    if REDIS_PASSWORD:
        CELERY_BROKER_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST_AND_PORT}/0"
    else:
        CELERY_BROKER_URL = f"redis://{REDIS_HOST_AND_PORT}/0"

CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = os.getenv("TIME_ZONE", "UTC")

# User provided Celery settings
CELERY_QUEUE_NAME = os.getenv("CELERY_QUEUE_NAME", "django_ninja_ready_to_go_queue")
CELERY_TASK_DEFAULT_QUEUE = CELERY_QUEUE_NAME
CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", 2))
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv("CELERY_PREFETCH_MULTIPLIER", 2))
CELERY_WORKER_POOL = os.getenv("CELERY_POOL", "gevent")
RUN_CELERY_TOGETHER = os.getenv("RUN_CELERY_TOGETHER", "false").lower() == "true"


# Dramatiq Configuration
DRAMATIQ_BROKER_URL = os.getenv("DRAMATIQ_BROKER_URL", CELERY_BROKER_URL)
DRAMATIQ_QUEUE_NAME = os.getenv("DRAMATIQ_QUEUE_NAME", "django_ninja_dramatiq_queue")
DRAMATIQ_WORKERS = int(os.getenv("DRAMATIQ_WORKERS", 2))
DRAMATIQ_WORKER_CONCURRENCY = int(os.getenv("DRAMATIQ_WORKER_CONCURRENCY", 2))
DRAMATIQ_PREFETCH_MULTIPLIER = int(os.getenv("DRAMATIQ_PREFETCH_MULTIPLIER", 2))
DRAMATIQ_POOL = os.getenv("DRAMATIQ_POOL", "gevent")
RUN_DRAMATIQ_TOGETHER = os.getenv("RUN_DRAMATIQ_TOGETHER", "false").lower() == "true"

try:
    import dramatiq
    from dramatiq.brokers.redis import RedisBroker

    from common.dramatiq_middleware import DjangoDBConnectionsMiddleware

    if DRAMATIQ_BROKER_URL:
        dramatiq_broker = RedisBroker(url=DRAMATIQ_BROKER_URL)
        dramatiq_broker.add_middleware(DjangoDBConnectionsMiddleware())
        dramatiq.set_broker(dramatiq_broker)
except ImportError:
    pass
