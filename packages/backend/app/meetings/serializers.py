from rest_framework import serializers

from app.models.client import Client
from app.models.meeting import Meeting


class MeetingSerializer(serializers.ModelSerializer):
    advisor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Meeting
        fields = ("id", "title", "date", "notes", "client", "advisor")

    def validate_client(self, client: Client) -> Client:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            msg = "Authentication required."
            raise serializers.ValidationError(msg)
        if client.advisor_id != user.pk:
            raise serializers.ValidationError("This client is not in your book.")
        return client
