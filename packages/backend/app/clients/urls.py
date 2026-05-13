from django.urls import include, path
from rest_framework.routers import DefaultRouter

from app.clients.views import ClientViewSet

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")

urlpatterns = [
    path("", include(router.urls)),
]
