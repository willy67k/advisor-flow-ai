"""RAG retrieval utilities — Step 5.3."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.accounts.models import User
from app.models.client import Client
from app.models.meeting import Meeting
from app.services.ai.retrieval import assemble_retrieved_context, retrieve_context_for_meeting_notes


@pytest.mark.django_db
def test_retrieve_skips_embedding_when_no_chunks():
    user = User.objects.create_user(username="rag_u", password="pw", role=User.Role.ADVISOR)
    c = Client.objects.create(name="Co", email="c@test", advisor=user)
    m = Meeting.objects.create(
        title="M",
        date="2026-01-02",
        notes="Discuss budget.",
        client=c,
        advisor=user,
    )

    with patch("app.services.ai.retrieval.embed_texts_batch") as emb:
        out = retrieve_context_for_meeting_notes(meeting_id=m.pk, query_text="hello agenda")
        emb.assert_not_called()
    assert out == ""


def test_assemble_retrieved_context_truncates_for_max_chars():
    doc = SimpleNamespace(file_name="memo.pdf")
    chunk = SimpleNamespace(document=doc, content="alpha " + "x" * 200)
    text = assemble_retrieved_context([chunk], max_chars=80)
    assert "memo.pdf" in text
    assert "alpha" in text
    assert len(text) <= 200
