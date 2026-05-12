from django.urls import path

from app.accounts.views import (
    AdvisorflowLoginView,
    AdvisorflowRefreshView,
    LogoutView,
    MeView,
    RegisterView,
)

urlpatterns = [
    path("login/", AdvisorflowLoginView.as_view(), name="auth-login"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("refresh/", AdvisorflowRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
