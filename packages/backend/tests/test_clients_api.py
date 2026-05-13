"""Client CRUD API — checklist Step 2.4."""

import pytest

from app.accounts.models import User
from app.models.client import Client


@pytest.fixture
def advisor_a(api_client):
    user = User.objects.create_user(username="adv_a", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/",
        {"username": "adv_a", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    token = login.json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return user


@pytest.fixture
def advisor_b(api_client):
    return User.objects.create_user(username="adv_b", password="pw", role=User.Role.ADVISOR)


@pytest.mark.django_db
def test_list_clients_empty_then_create(api_client, advisor_a):
    empty = api_client.get("/api/clients/").json()
    assert empty["results"] == []

    resp = api_client.post(
        "/api/clients/",
        {"name": "Acme", "email": "contact@acme.test", "phone": "+15551234567"},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme"
    assert body["email"] == "contact@acme.test"
    assert body["phone"] == "+15551234567"
    assert body["advisor"] == advisor_a.pk

    listed = api_client.get("/api/clients/").json()
    assert len(listed["results"]) == 1
    assert listed["results"][0]["id"] == body["id"]


@pytest.mark.django_db
def test_retrieve_patch_delete_client(api_client, advisor_a):
    c = Client.objects.create(
        name="Beta",
        email="b@beta.test",
        phone="",
        advisor=advisor_a,
    )
    got = api_client.get(f"/api/clients/{c.pk}/")
    assert got.status_code == 200
    assert got.json()["name"] == "Beta"

    patched = api_client.patch(
        f"/api/clients/{c.pk}/",
        {"phone": "999"},
        format="json",
    )
    assert patched.status_code == 200
    assert patched.json()["phone"] == "999"

    deleted = api_client.delete(f"/api/clients/{c.pk}/")
    assert deleted.status_code == 204
    assert api_client.get(f"/api/clients/{c.pk}/").status_code == 404


@pytest.mark.django_db
def test_other_advisor_clients_are_invisible(api_client, advisor_a, advisor_b):
    mine = Client.objects.create(
        name="Mine",
        email="mine@test",
        advisor=advisor_a,
    )
    theirs = Client.objects.create(
        name="Theirs",
        email="theirs@test",
        advisor=advisor_b,
    )

    resp_other = api_client.get(f"/api/clients/{theirs.pk}/")
    assert resp_other.status_code == 404

    patch_other = api_client.patch(f"/api/clients/{theirs.pk}/", {"name": "X"}, format="json")
    assert patch_other.status_code == 404

    del_other = api_client.delete(f"/api/clients/{theirs.pk}/")
    assert del_other.status_code == 404

    listed = api_client.get("/api/clients/").json()
    ids = {row["id"] for row in listed["results"]}
    assert mine.pk in ids
    assert theirs.pk not in ids


@pytest.mark.django_db
def test_unauthenticated_requests_rejected(api_client):
    assert api_client.get("/api/clients/").status_code == 401
    assert (
        api_client.post(
            "/api/clients/", {"name": "N", "email": "e@test"}, format="json"
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_create_rejects_invalid_email(api_client, advisor_a):
    resp = api_client.post(
        "/api/clients/",
        {"name": "Bad", "email": "not-an-email"},
        format="json",
    )
    assert resp.status_code == 400
