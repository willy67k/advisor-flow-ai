"""Pure tests for deterministic chat scope gate."""

import pytest

from app.chat.chat_scope import user_message_covers_workspace_scope


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("What is the capital of France?", False),
        ("Write me a poem about cats", False),
        ("Explain quantum mechanics", False),
        ("Tell me a joke", False),
        ("How should I prepare for a client review meeting?", True),
        ("Can I upload this PDF to the workflow?", True),
        ("請幫我整理會議摘要的重點", True),
        ("這份合規文件要怎麼送簽核？", True),
        ("", False),
        ("   hi   ", False),
        ("ab", False),
    ],
)
def test_workspace_scope_gate(text, expected):
    assert user_message_covers_workspace_scope(text) is expected
