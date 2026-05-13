from rest_framework import serializers

from app.models.document import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "file_name", "status", "meeting")
