from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from app.clients.serializers import ClientSerializer
from app.models.client import Client


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
