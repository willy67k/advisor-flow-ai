"""Meeting-summary workflow prompts — versioned templates for Step 3.5."""

from __future__ import annotations

# Summarize node (gateway `complete_chat` system message)
VERSION_SUMMARIZE_SYSTEM = "1"
TEMPLATE_SUMMARIZE_SYSTEM = (
    "You summarize financial-advisor meeting notes for internal records. "
    "Use concise bullet prose; preserve names, figures, deadlines, risks, decisions."
)

# Action-items node (instructor structured extraction system message)
VERSION_ACTION_ITEMS_SYSTEM = "1"
TEMPLATE_ACTION_ITEMS_SYSTEM = (
    "You extract clear action items from meeting materials. Each item must describe "
    "a single follow-up task. Normalize wording; duplicate tasks may be omitted."
)
