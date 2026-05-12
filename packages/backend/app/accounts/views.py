from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from app.accounts.serializers import (
    AdvisorflowTokenObtainPairSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
)


class AdvisorflowLoginView(TokenObtainPairView):
    serializer_class = AdvisorflowTokenObtainPairSerializer
    authentication_classes = ()


class RegisterView(APIView):
    """Creates an ``advisor`` account and returns a JWT pair (same shape as login + ``user``)."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = AdvisorflowTokenObtainPairSerializer.get_token(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class AdvisorflowRefreshView(TokenRefreshView):
    authentication_classes = ()


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    """Blacklist the presented refresh token (requires ``token_blacklist`` app)."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw = serializer.validated_data["refresh"]
        try:
            token = RefreshToken(raw)
            token.blacklist()
        except (TokenError, InvalidToken):
            pass
        return Response(status=205)
