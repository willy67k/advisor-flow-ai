from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.clients.serializers import ClientSerializer
from app.meetings.serializers import MeetingSerializer
from app.models.client import Client
from app.models.meeting import Meeting


class ClientPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ClientViewSet(viewsets.ModelViewSet):
    """CRUD for the authenticated user's clients only."""

    serializer_class = ClientSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ClientPagination
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        return Client.objects.filter(advisor=self.request.user)

    def perform_create(self, serializer):
        serializer.save(advisor=self.request.user)

    @action(detail=True, methods=["get"], url_path="meetings")
    def meetings(self, request, pk=None):
        """Meetings for this client (same advisor)."""
        client = self.get_object()
        qs = Meeting.objects.filter(client=client, advisor=request.user).select_related("client")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MeetingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MeetingSerializer(qs, many=True)
        return Response(serializer.data)
