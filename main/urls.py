"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.http import Http404
from django.urls import path
from ninja import NinjaAPI, Router

# Create a global API instance
api = NinjaAPI(title="My Project API")


@api.exception_handler(Http404)
def on_404(request, exc):
    return api.create_response(
        request,
        {
            "error": {"message": "Not Found"},
            "trace_id": getattr(request, "trace_id", None),
            "data": None,
        },
        status=404,
    )


# Include routers from each app
from apps.animals_app.v1.views import router as animals_router  # noqa
from apps.files_app.v1.views import router as files_router  # noqa

# Import ping sub-routers
from apps.ping_app.v1.views import (  # noqa
    cache_router,
    database_router,
    external_router,
    system_router,
    tasks_router,
)
from apps.users_app.v1.views import router as users_router  # noqa

api.add_router("/v1/animals/", animals_router, tags=["Animals"])
api.add_router("/v1/users/", users_router, tags=["Users"])
api.add_router("/v1/files/", files_router, tags=["Files Reference"])

# Include ping routers with separate prefixes (matching FastAPI pattern)
api.add_router("/v1/pings/", system_router, tags=["ping-health"])
api.add_router("/v1/pings/cache/", cache_router, tags=["cache-pings"])
api.add_router("/v1/pings/db/", database_router, tags=["database-pings"])
api.add_router("/v1/pings/external/", external_router, tags=["external-pings"])
api.add_router("/v1/tasks/", tasks_router, tags=["background-tasks"])


# Catch-all for unmatched API routes
catch_all_router = Router()


@catch_all_router.api_operation(
    ["GET", "POST", "PUT", "DELETE", "PATCH"], "/{path:path}", include_in_schema=False
)
def catch_all(request, path: str):
    return api.create_response(
        request,
        {
            "error": {"message": "Not Found"},
            "trace_id": getattr(request, "trace_id", None),
            "data": None,
        },
        status=404,
    )


api.add_router("", catch_all_router)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
