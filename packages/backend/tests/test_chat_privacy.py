"""Copilot privacy prompt composition."""

from __future__ import annotations

from app.accounts.models import User
from app.chat.privacy import compose_chat_system_prompt


def test_advisor_prompt_includes_own_book_fence() -> None:
    u = User(role=User.Role.ADVISOR)
    text = compose_chat_system_prompt(u)
    assert "authenticated as an **advisor**" in text


def test_compliance_prompt_skips_advisor_own_book_fence() -> None:
    u = User(role=User.Role.COMPLIANCE_OFFICER)
    text = compose_chat_system_prompt(u)
    assert "authenticated as an **advisor**" not in text
