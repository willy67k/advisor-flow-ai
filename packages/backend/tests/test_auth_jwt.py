"""JWT authentication flow (SimpleJWT)."""

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from app.accounts.models import User


@pytest.mark.django_db
def test_login_success_returns_tokens_and_embeds_role_claim(api_client):
    User.objects.create_user(
        username="ada",
        email="ada@example.com",
        password="sekrit12",
        role=User.Role.MANAGER,
    )
    resp = api_client.post(
        "/api/auth/login/",
        {"username": "ada", "password": "sekrit12"},
        format="json",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access" in body and "refresh" in body

    decoded = AccessToken(body["access"])
    assert decoded["role"] == User.Role.MANAGER


@pytest.mark.django_db
def test_login_rejects_bad_password(api_client):
    User.objects.create_user(username="bob", password="right", role=User.Role.ADVISOR)
    resp = api_client.post(
        "/api/auth/login/",
        {"username": "bob", "password": "wrong"},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_me_returns_role_with_valid_access(api_client):
    User.objects.create_user(
        username="cara",
        email="cara@example.com",
        password="pwd",
        role=User.Role.COMPLIANCE_OFFICER,
    )
    login = api_client.post(
        "/api/auth/login/",
        {"username": "cara", "password": "pwd"},
        format="json",
    )
    token = login.json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    me = api_client.get("/api/auth/me/")
    assert me.status_code == 200
    data = me.json()
    assert data["username"] == "cara"
    assert data["role"] == User.Role.COMPLIANCE_OFFICER


@pytest.mark.django_db
def test_me_rejects_missing_or_bad_access_token(api_client):
    resp = api_client.get("/api/auth/me/")
    assert resp.status_code == 401

    api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-jwt-token")
    assert api_client.get("/api/auth/me/").status_code == 401


@pytest.mark.django_db
def test_refresh_issues_new_access(api_client):
    User.objects.create_user(username="dan", password="pw", role=User.Role.ADVISOR)
    body = api_client.post(
        "/api/auth/login/",
        {"username": "dan", "password": "pw"},
        format="json",
    ).json()
    refreshed = api_client.post(
        "/api/auth/refresh/",
        {"refresh": body["refresh"]},
        format="json",
    )
    assert refreshed.status_code == 200
    assert "access" in refreshed.json()


@pytest.mark.django_db
def test_logout_blacklists_refresh_so_refresh_returns_401(api_client):
    User.objects.create_user(username="eve", password="pw", role=User.Role.ADVISOR)
    tokens = api_client.post(
        "/api/auth/login/",
        {"username": "eve", "password": "pw"},
        format="json",
    ).json()
    out = api_client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
    assert out.status_code == 205

    reused = api_client.post(
        "/api/auth/refresh/",
        {"refresh": tokens["refresh"]},
        format="json",
    )
    assert reused.status_code == 401


@pytest.mark.django_db
def test_register_creates_advisor_returns_tokens_and_user(api_client):
    resp = api_client.post(
        "/api/auth/register/",
        {
            "username": "finn",
            "email": "finn@example.com",
            "password": "RiverBank9!",
            "password_confirm": "RiverBank9!",
        },
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["username"] == "finn"
    assert body["user"]["role"] == User.Role.ADVISOR

    decoded = AccessToken(body["access"])
    assert decoded["role"] == User.Role.ADVISOR


@pytest.mark.django_db
def test_register_rejects_duplicate_username(api_client):
    User.objects.create_user(
        username="dup",
        email="a@example.com",
        password="RiverBank9!",
        role=User.Role.ADVISOR,
    )
    resp = api_client.post(
        "/api/auth/register/",
        {
            "username": "dup",
            "email": "b@example.com",
            "password": "RiverBank9!",
            "password_confirm": "RiverBank9!",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_register_rejects_password_mismatch(api_client):
    resp = api_client.post(
        "/api/auth/register/",
        {
            "username": "gigi",
            "email": "gigi@example.com",
            "password": "RiverBank9!",
            "password_confirm": "OtherPass9!",
        },
        format="json",
    )
    assert resp.status_code == 400
