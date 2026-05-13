from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from app.meetings.serializers import MeetingSerializer
from app.models.meeting import Meeting


class MeetingPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class MeetingViewSet(viewsets.ModelViewSet):
    """CRUD for meetings owned by the authenticated advisor (via ``client``)."""

    serializer_class = MeetingSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = MeetingPagination
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        return Meeting.objects.filter(advisor=self.request.user).select_related("client")

    def perform_create(self, serializer):
        serializer.save(advisor=self.request.user)
