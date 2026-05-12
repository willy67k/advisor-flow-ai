from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role")


class RegisterSerializer(serializers.ModelSerializer):
    """Public sign-up — new accounts default to ``advisor`` (no privileged self-serve roles)."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=1)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirm")

    def validate_username(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            msg = "Username cannot be blank."
            raise serializers.ValidationError(msg)
        if User.objects.filter(username__iexact=cleaned).exists():
            raise serializers.ValidationError("This username is already taken.")
        return cleaned

    def validate_email(self, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            msg = "Email is required."
            raise serializers.ValidationError(msg)
        if User.objects.filter(email__iexact=cleaned).exists():
            raise serializers.ValidationError("This email is already registered.")
        return cleaned

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        password = attrs.get("password")
        confirm = attrs.pop("password_confirm", None)
        if password != confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."},
            )
        try:
            validate_password(str(password))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data: dict[str, object]) -> User:
        password = validated_data.pop("password")
        return User.objects.create_user(role=User.Role.ADVISOR, password=password, **validated_data)


class AdvisorflowTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds ``role`` to access (and refresh) token claims."""

    @classmethod
    def get_token(cls, user):  # type: ignore[override]
        token = super().get_token(user)
        token["role"] = getattr(user, "role", "")
        return token


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)
