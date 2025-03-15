from django.urls import path
from ninja import NinjaAPI

from .views import router as animal_router

api = NinjaAPI()

api.add_router("/animals/", animal_router)

urlpatterns = [
    path("api/", api.urls),
]
