from django.urls import path

from app.observability.views import ObservabilityLogListView

urlpatterns = [
    path("observability-logs/", ObservabilityLogListView.as_view()),
]
