"""Root URL configuration."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/auth/", include("app.accounts.urls")),
    path("api/", include("app.clients.urls")),
    path("api/", include("app.meetings.urls")),
    path("api/", include("app.documents.urls")),
    path("api/", include("app.workflows.urls")),
    path("api/", include("app.approvals.urls")),
    path("api/", include("app.compliance.urls")),
]
