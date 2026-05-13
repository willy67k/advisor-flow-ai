"""Meeting summary LangGraph workflow — checklist Step 3.2."""

from __future__ import annotations

import logging
from typing import Any, TypedDict, cast

from instructor import patch
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from app.config.env import get_env
from app.services.ai.gateway import ChatMessage, LLMProvider, complete_chat

logger = logging.getLogger(__name__)


class MeetingActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    task: str = Field(description="Concrete follow-up extracted from the meeting.")
    owner: str | None = Field(default=None, description="Responsible party if stated.")
    due: str | None = Field(default=None, description="Due date / timeframe if stated.")


class MeetingSummaryOutput(BaseModel):
    """Final structured result: narrative summary plus action items."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    action_items: list[MeetingActionItem] = Field(default_factory=list)


class _ActionItemsStructured(BaseModel):
    """Instructor envelope (root object for structured completions)."""

    model_config = ConfigDict(extra="forbid")

    action_items: list[MeetingActionItem] = Field(default_factory=list)


class MeetingWorkflowState(TypedDict, total=False):
    """LangGraph shared state."""

    notes: str
    summary: str
    action_items: list[dict[str, Any]]


def _llm_summarize_notes(notes: str) -> str:
    msgs = [
        ChatMessage(role="system", content=_SUMMARY_SYSTEM),
        ChatMessage(
            role="user",
            content=f"Meeting notes:\n\n{notes}\n\nWrite the summary only.",
        ),
    ]
    result = complete_chat(
        msgs,
        provider=LLMProvider.OPENAI,
        temperature=0.2,
    )
    return result.content.strip()


def _llm_extract_action_items(*, notes: str, summary: str) -> list[MeetingActionItem]:
    env = get_env()
    key = env.openai_api_key
    if not key:
        msg = "OPENAI_API_KEY is required for instructor structured action-item extraction."
        raise RuntimeError(msg)

    client = patch(OpenAI(api_key=key))

    payload = (
        "Original notes:\n"
        f"{notes}\n\n"
        "Summary for context:\n"
        f"{summary}\n\n"
        "Extract actionable follow-ups; omit vague items."
    )

    extraction = cast(
        _ActionItemsStructured,
        client.chat.completions.create(
            model=env.ai_openai_default_model,
            response_model=_ActionItemsStructured,
            messages=[
                {"role": "system", "content": _ACTION_ITEMS_SYSTEM},
                {"role": "user", "content": payload},
            ],
            temperature=0.1,
        ),
    )
    return list(extraction.action_items)


_SUMMARY_SYSTEM = (
    "You summarize financial-advisor meeting notes for internal records. "
    "Use concise bullet prose; preserve names, figures, deadlines, risks, decisions."
)

_ACTION_ITEMS_SYSTEM = (
    "You extract clear action items from meeting materials. Each item must describe "
    "a single follow-up task. Normalize wording; duplicate tasks may be omitted."
)


def _node_generate_summary(state: MeetingWorkflowState) -> MeetingWorkflowState:
    notes = state.get("notes", "").strip()
    if not notes:
        logger.warning("meeting_summary: empty notes; skipping LLM summarize.")
        return {"summary": ""}
    summary = _llm_summarize_notes(notes)
    return {"summary": summary}


def _node_extract_action_items(state: MeetingWorkflowState) -> MeetingWorkflowState:
    notes = state.get("notes", "")
    summary = state.get("summary", "")
    if not summary.strip():
        return {"action_items": []}

    raw_items = _llm_extract_action_items(notes=notes, summary=summary)
    return {"action_items": [item.model_dump() for item in raw_items]}


def build_meeting_summary_graph() -> CompiledStateGraph:
    """Compiled graph: ``START → generate_summary → extract_action_items → END``."""
    workflow = StateGraph(MeetingWorkflowState)
    workflow.add_node("generate_summary", _node_generate_summary)
    workflow.add_node("extract_action_items", _node_extract_action_items)
    workflow.add_edge(START, "generate_summary")
    workflow.add_edge("generate_summary", "extract_action_items")
    workflow.add_edge("extract_action_items", END)
    return workflow.compile()


def run_meeting_summary_workflow(
    notes: str,
    *,
    graph: CompiledStateGraph | None = None,
) -> MeetingSummaryOutput:
    """Invoke the meeting-summary graph and return validated structured output."""
    compiled = graph or build_meeting_summary_graph()
    final_state = compiled.invoke(cast(MeetingWorkflowState, {"notes": notes}))

    summary = str(final_state.get("summary") or "").strip()
    raw_items = final_state.get("action_items") or []
    items = [MeetingActionItem.model_validate(d) for d in raw_items]
    return MeetingSummaryOutput(summary=summary, action_items=items)
