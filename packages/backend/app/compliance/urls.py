"""Compliance URLs — Step 7.1."""

from django.urls import path

from app.compliance.views import (
    CompliancePendingListView,
    ComplianceWorkflowClearView,
    ComplianceWorkflowRejectView,
)

urlpatterns = [
    path("compliance/pending", CompliancePendingListView.as_view()),
    path("compliance/workflows/<int:pk>/clear", ComplianceWorkflowClearView.as_view()),
    path("compliance/workflows/<int:pk>/reject", ComplianceWorkflowRejectView.as_view()),
]
