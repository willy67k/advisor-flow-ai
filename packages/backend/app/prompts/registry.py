"""Prompt registry: single entry point for versioned templates (Step 3.5)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.prompts import meeting_summary as meeting_summary_prompts


@dataclass(frozen=True)
class PromptSpec:
    """Registered prompt: stable key, semver-style version string, body template."""

    key: str
    version: str
    template: str


class PromptKey(StrEnum):
    """Stable IDs for prompts consumed by workflows and services."""

    MEETING_SUMMARY_SUMMARIZE_SYSTEM = "meeting_summary.summarize_system"
    MEETING_SUMMARY_ACTION_ITEMS_SYSTEM = "meeting_summary.action_items_system"


_SPECS: Final[dict[PromptKey, PromptSpec]] = {
    PromptKey.MEETING_SUMMARY_SUMMARIZE_SYSTEM: PromptSpec(
        key=PromptKey.MEETING_SUMMARY_SUMMARIZE_SYSTEM.value,
        version=meeting_summary_prompts.VERSION_SUMMARIZE_SYSTEM,
        template=meeting_summary_prompts.TEMPLATE_SUMMARIZE_SYSTEM,
    ),
    PromptKey.MEETING_SUMMARY_ACTION_ITEMS_SYSTEM: PromptSpec(
        key=PromptKey.MEETING_SUMMARY_ACTION_ITEMS_SYSTEM.value,
        version=meeting_summary_prompts.VERSION_ACTION_ITEMS_SYSTEM,
        template=meeting_summary_prompts.TEMPLATE_ACTION_ITEMS_SYSTEM,
    ),
}


def get_prompt_spec(key: PromptKey) -> PromptSpec:
    return _SPECS[key]


def prompt_template(key: PromptKey) -> str:
    """Return the template body for LLM system prompts."""
    return _SPECS[key].template
