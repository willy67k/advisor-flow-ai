"""Document upload and retrieval."""

from __future__ import annotations

import uuid
from pathlib import Path

from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.documents.serializers import DocumentSerializer
from app.documents.tasks import process_document_task
from app.models.document import Document
from app.models.meeting import Meeting

ALLOWED_EXTENSIONS = frozenset({".pdf", ".doc", ".docx"})
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class DocumentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class DocumentListView(generics.ListAPIView):
    """List documents for meetings owned by the caller; optional ``?meeting=<id>`` filter."""

    permission_classes = (IsAuthenticated,)
    serializer_class = DocumentSerializer
    pagination_class = DocumentPagination

    def get_queryset(self):
        qs = Document.objects.filter(meeting__advisor=self.request.user).select_related("meeting")
        meeting_raw = self.request.query_params.get("meeting")
        if meeting_raw is None:
            return qs
        try:
            meeting_id = int(meeting_raw)
        except (TypeError, ValueError):
            return Document.objects.none()
        return qs.filter(meeting_id=meeting_id)


class DocumentUploadView(APIView):
    """Multipart upload: ``meeting`` + ``file`` (PDF / Word)."""

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        errors: dict[str, list[str]] = {}
        meeting_raw = request.data.get("meeting")
        upload = request.FILES.get("file")
        if meeting_raw is None:
            errors["meeting"] = ["This field is required."]
        if upload is None:
            errors["file"] = ["No file submitted."]
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            meeting_id = int(meeting_raw)
        except (TypeError, ValueError):
            return Response(
                {"meeting": ["Invalid meeting id."]}, status=status.HTTP_400_BAD_REQUEST
            )

        meeting = Meeting.objects.filter(pk=meeting_id, advisor=request.user).first()
        if meeting is None:
            return Response({"meeting": ["Meeting not found."]}, status=status.HTTP_404_NOT_FOUND)

        original_name = get_valid_filename(upload.name)
        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return Response(
                {"file": ["Only PDF and Word (.doc, .docx) files are allowed."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        size = getattr(upload, "size", None)
        if size is not None and size > MAX_UPLOAD_BYTES:
            return Response({"file": ["File too large."]}, status=status.HTTP_400_BAD_REQUEST)

        if ext == ".pdf":
            head = upload.read(5)
            upload.seek(0)
            if not head.startswith(b"%PDF"):
                return Response(
                    {"file": ["Invalid PDF content."]}, status=status.HTTP_400_BAD_REQUEST
                )

        stored_rel = f"documents/meetings/{meeting.pk}/{uuid.uuid4().hex}{ext}"
        saved_path = default_storage.save(stored_rel, upload)

        doc = Document.objects.create(
            file_name=original_name,
            file_path=saved_path,
            status=Document.Status.UPLOADED,
            meeting=meeting,
        )
        process_document_task.delay(int(doc.pk))
        doc.refresh_from_db()
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.RetrieveAPIView):
    """Lookup by id; restricted to documents under the caller's meetings."""

    permission_classes = (IsAuthenticated,)
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(meeting__advisor=self.request.user).select_related("meeting")
