from django.urls import path

from app.chat.views import ChatStreamView

urlpatterns = [
    path("stream", ChatStreamView.as_view()),
    path("stream/", ChatStreamView.as_view()),
]
