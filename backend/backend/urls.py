from core.api import router as auth_router
from django.contrib import admin
from django.urls import path

# ninja
from ninja import NinjaAPI

api = NinjaAPI(
    title="core api",
    description="core api endpoint",
)

api.add_router("/auth", router=auth_router, tags=["Authentcaion"])

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
