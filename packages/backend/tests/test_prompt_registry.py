"""Prompt registry (Step 3.5)."""

from __future__ import annotations

import pytest

from app.prompts import PromptKey, get_prompt_spec, prompt_template


@pytest.mark.parametrize(
    "key",
    [
        PromptKey.MEETING_SUMMARY_SUMMARIZE_SYSTEM,
        PromptKey.MEETING_SUMMARY_ACTION_ITEMS_SYSTEM,
    ],
)
def test_registered_prompts_have_version_and_non_empty_template(key: PromptKey) -> None:
    spec = get_prompt_spec(key)
    assert spec.key == key.value
    assert spec.version
    assert spec.template.strip()
    assert prompt_template(key) == spec.template
