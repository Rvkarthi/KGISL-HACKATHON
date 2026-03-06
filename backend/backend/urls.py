from ats.api import router as ats_router
from ats.jd_api import router as jd_router

# routers
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
api.add_router("/ats", router=ats_router, tags=["Ats"])
api.add_router("/jd", router=jd_router, tags=["JD"])

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
