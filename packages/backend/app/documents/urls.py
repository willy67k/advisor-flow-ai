from django.urls import path

from app.documents.views import (
    DocumentDetailView,
    DocumentListView,
    DocumentUploadView,
)

urlpatterns = [
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("documents/upload", DocumentUploadView.as_view(), name="document-upload-no-slash"),
    path("documents/<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path("documents/<int:pk>", DocumentDetailView.as_view(), name="document-detail-no-slash"),
]
