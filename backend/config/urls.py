from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from api.views import (
    ItemViewSet,
    RequestCreateView,
    StatusListView,
    TokenLoginView,
    TokenLogoutView,
    health_check,
)

router = DefaultRouter()
router.register("items", ItemViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/auth/login/", TokenLoginView.as_view(), name="token-login"),
    path("api/auth/logout/", TokenLogoutView.as_view(), name="token-logout"),
    path("api/requests/", RequestCreateView.as_view(), name="request-create"),
    path("api/statuses/", StatusListView.as_view(), name="status-list"),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(
            authentication_classes=[],
            permission_classes=[],
        ),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[],
            permission_classes=[],
        ),
        name="swagger-ui",
    ),
    path("api/", include(router.urls)),
]
