"""Document upload + detail — checklist Step 2.6."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from app.accounts.models import User
from app.models.client import Client
from app.models.document import Document
from app.models.meeting import Meeting


@pytest.fixture(autouse=True)
def _media_root(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def advisor_auth(api_client):
    user = User.objects.create_user(username="doc_adv", password="pw", role=User.Role.ADVISOR)
    login = api_client.post(
        "/api/auth/login/",
        {"username": "doc_adv", "password": "pw"},
        format="json",
    )
    assert login.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    return user


@pytest.fixture
def meeting(advisor_auth):
    client = Client.objects.create(
        name="Acme",
        email="acme@test",
        advisor=advisor_auth,
    )
    return Meeting.objects.create(
        title="Sync",
        date="2026-06-01",
        notes="",
        client=client,
        advisor=advisor_auth,
    )


@pytest.mark.django_db
def test_upload_pdf_creates_document_record(api_client, advisor_auth, meeting):
    pdf = SimpleUploadedFile(
        "notes.pdf",
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n",
        content_type="application/pdf",
    )
    resp = api_client.post(
        "/api/documents/upload/",
        {"meeting": str(meeting.pk), "file": pdf},
        format="multipart",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == Document.Status.UPLOADED
    assert body["meeting"] == meeting.pk
    assert "id" in body
    assert Document.objects.filter(pk=body["id"]).exists()

    detail = api_client.get(f"/api/documents/{body['id']}/")
    assert detail.status_code == 200
    assert detail.json()["file_name"] == "notes.pdf"
    assert detail.json()["status"] == Document.Status.UPLOADED


@pytest.mark.django_db
def test_upload_without_trailing_slash(api_client, meeting):
    """Avoid APPEND_SLASH POST redirect crash when callers omit the final slash."""
    pdf = SimpleUploadedFile(
        "slash.pdf",
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n",
        content_type="application/pdf",
    )
    resp = api_client.post(
        "/api/documents/upload",
        {"meeting": str(meeting.pk), "file": pdf},
        format="multipart",
    )
    assert resp.status_code == 201


@pytest.mark.django_db
def test_upload_rejects_wrong_extension(api_client, meeting):
    bad = SimpleUploadedFile("x.txt", b"hello", content_type="text/plain")
    resp = api_client.post(
        "/api/documents/upload/",
        {"meeting": str(meeting.pk), "file": bad},
        format="multipart",
    )
    assert resp.status_code == 400
    assert "file" in resp.json()


@pytest.mark.django_db
def test_upload_rejects_pdf_magic(api_client, meeting):
    fake = SimpleUploadedFile(
        "fake.pdf",
        b"not a pdf",
        content_type="application/pdf",
    )
    resp = api_client.post(
        "/api/documents/upload/",
        {"meeting": str(meeting.pk), "file": fake},
        format="multipart",
    )
    assert resp.status_code == 400
    assert "file" in resp.json()


@pytest.mark.django_db
def test_upload_docx_by_extension_allowed(api_client, meeting):
    docx = SimpleUploadedFile(
        "memo.docx",
        b"PK\x03\x04fake-docx-bytes",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    resp = api_client.post(
        "/api/documents/upload/",
        {"meeting": str(meeting.pk), "file": docx},
        format="multipart",
    )
    assert resp.status_code == 201
    assert resp.json()["file_name"] == "memo.docx"


@pytest.mark.django_db
def test_detail_not_found_for_other_users_document(api_client, advisor_auth, meeting):
    other = User.objects.create_user(username="other_adv", password="pw", role=User.Role.ADVISOR)
    other_meeting = Meeting.objects.create(
        title="Other",
        date="2026-06-02",
        notes="",
        client=Client.objects.create(name="X", email="x@test", advisor=other),
        advisor=other,
    )
    doc = Document.objects.create(
        file_name="a.pdf",
        file_path="documents/meetings/9/x.pdf",
        meeting=other_meeting,
    )

    assert api_client.get(f"/api/documents/{doc.pk}/").status_code == 404
