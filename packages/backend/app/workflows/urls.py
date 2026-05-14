from django.urls import path

from app.workflows.views import WorkflowDetailView, WorkflowListView, WorkflowStartView

urlpatterns = [
    path("workflows/", WorkflowListView.as_view()),
    path("workflows/start", WorkflowStartView.as_view()),
    path("workflows/<int:pk>", WorkflowDetailView.as_view()),
]
