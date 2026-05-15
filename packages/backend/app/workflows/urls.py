from django.urls import path

from app.workflows.views import (
    AuditLogListView,
    WorkflowDetailView,
    WorkflowListView,
    WorkflowStartView,
)

urlpatterns = [
    path("workflows/", WorkflowListView.as_view()),
    path("workflows/start", WorkflowStartView.as_view()),
    path("workflows/<int:pk>", WorkflowDetailView.as_view()),
    path("audit-logs/", AuditLogListView.as_view()),
]
