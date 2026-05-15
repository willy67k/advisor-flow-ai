"""Observability log API — managers only (Phase 8.2 UI)."""

from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from app.accounts.permissions import IsManager
from app.models.observability_log import ObservabilityLog
from app.observability.serializers import ObservabilityLogSerializer


class ObservabilityLogPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 50


class ObservabilityLogListView(ListAPIView):
    permission_classes = (IsAuthenticated, IsManager)
    serializer_class = ObservabilityLogSerializer
    pagination_class = ObservabilityLogPagination

    def get_queryset(self):
        qs = ObservabilityLog.objects.all()
        cat = self.request.query_params.get("category")
        sev = self.request.query_params.get("severity")
        if cat:
            qs = qs.filter(category=str(cat))
        if sev:
            qs = qs.filter(severity=str(sev))
        return qs.order_by("-id")
