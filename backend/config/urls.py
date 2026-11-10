from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import ItemViewSet
from api.views import health_check

router = DefaultRouter()
router.register("items", ItemViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/", include(router.urls)),
]
