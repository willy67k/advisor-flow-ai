from django.urls import include, path
from rest_framework.routers import DefaultRouter

from app.meetings.views import MeetingViewSet

router = DefaultRouter()
router.register("meetings", MeetingViewSet, basename="meeting")

urlpatterns = [
    path("", include(router.urls)),
]
