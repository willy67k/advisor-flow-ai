from django.urls import path

from app.workflows.views import WorkflowDetailView, WorkflowStartView

urlpatterns = [
    path("workflows/start", WorkflowStartView.as_view()),
    path("workflows/<int:pk>", WorkflowDetailView.as_view()),
]
