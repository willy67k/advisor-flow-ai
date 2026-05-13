"""Meeting CRUD + nested client meetings — checklist Step 2.5."""

import pytest

from app.accounts.models import User
from app.models.client import Client
from app.models.meeting import Meeting


@pytest.fixture
def advisor_a(api_client):
    user = User.objects.create_user(username="m_adv_a", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/",
        {"username": "m_adv_a", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    token = login.json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return user


@pytest.fixture
def client_for_a(advisor_a):
    return Client.objects.create(
        name="Corp",
        email="corp@test",
        phone="",
        advisor=advisor_a,
    )


@pytest.fixture
def advisor_b():
    return User.objects.create_user(username="m_adv_b", password="pw", role=User.Role.ADVISOR)


@pytest.mark.django_db
def test_meeting_crud(api_client, advisor_a, client_for_a):
    empty = api_client.get("/api/meetings/").json()
    assert empty["results"] == []

    resp = api_client.post(
        "/api/meetings/",
        {
            "title": "Q1 Review",
            "date": "2026-05-01",
            "notes": "Discussed allocation.",
            "client": client_for_a.pk,
        },
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Q1 Review"
    assert body["client"] == client_for_a.pk
    assert body["advisor"] == advisor_a.pk

    mid = body["id"]
    got = api_client.get(f"/api/meetings/{mid}/")
    assert got.status_code == 200
    assert got.json()["notes"] == "Discussed allocation."

    patched = api_client.patch(
        f"/api/meetings/{mid}/", {"title": "Q1 Review (updated)"}, format="json"
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "Q1 Review (updated)"

    deleted = api_client.delete(f"/api/meetings/{mid}/")
    assert deleted.status_code == 204
    assert api_client.get(f"/api/meetings/{mid}/").status_code == 404


@pytest.mark.django_db
def test_meeting_rejects_other_users_client(api_client, advisor_a, advisor_b):
    other_client = Client.objects.create(
        name="Other",
        email="other@test",
        advisor=advisor_b,
    )
    resp = api_client.post(
        "/api/meetings/",
        {"title": "X", "date": "2026-01-01", "client": other_client.pk},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_other_advisor_meetings_hidden(api_client, advisor_a, advisor_b, client_for_a):
    m = Meeting.objects.create(
        title="Private",
        date="2026-03-15",
        notes="",
        client=client_for_a,
        advisor=advisor_a,
    )
    api_client.credentials()  # logout
    login_b = api_client.post(
        "/api/auth/login/",
        {"username": "m_adv_b", "password": "pw"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_b.json()['access']}")

    assert api_client.get(f"/api/meetings/{m.pk}/").status_code == 404
    listed = api_client.get("/api/meetings/").json()
    assert all(row["id"] != m.pk for row in listed["results"])


@pytest.mark.django_db
def test_client_meetings_nested_list(api_client, advisor_a, client_for_a):
    Meeting.objects.create(
        title="A",
        date="2026-04-01",
        notes="",
        client=client_for_a,
        advisor=advisor_a,
    )
    Meeting.objects.create(
        title="B",
        date="2026-04-02",
        notes="",
        client=client_for_a,
        advisor=advisor_a,
    )
    resp = api_client.get(f"/api/clients/{client_for_a.pk}/meetings/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2
    titles = {row["title"] for row in data["results"]}
    assert titles == {"A", "B"}


@pytest.mark.django_db
def test_client_meetings_nested_not_found_for_other_client(api_client, advisor_a, advisor_b):
    other = Client.objects.create(name="X", email="x@test", advisor=advisor_b)
    assert api_client.get(f"/api/clients/{other.pk}/meetings/").status_code == 404
