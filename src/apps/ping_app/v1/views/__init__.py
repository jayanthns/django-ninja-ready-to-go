from .cache_views import router as cache_router
from .database_views import router as database_router
from .external_views import router as external_router
from .system_views import router as system_router

__all__ = ["cache_router", "database_router", "external_router", "system_router"]
