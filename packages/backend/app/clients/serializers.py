from rest_framework import serializers

from app.models.client import Client


class ClientSerializer(serializers.ModelSerializer):
    advisor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Client
        fields = ("id", "name", "email", "phone", "advisor")
