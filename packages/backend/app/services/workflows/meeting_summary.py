"""Meeting summary LangGraph workflow — Steps 3.2 + 4.1 (human approval interrupt)."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypedDict, cast

from instructor import patch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from app.config.env import get_env
from app.prompts import PromptKey, prompt_template
from app.services.ai.gateway import ChatMessage, LLMProvider, complete_chat

logger = logging.getLogger(__name__)

_APPROVAL_ACTION_APPROVE = "approve"
_APPROVAL_ACTION_REJECT = "reject"

_APPROVAL_RESULT_APPROVED = "approved"
_APPROVAL_RESULT_REJECTED = "rejected"


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
    approval_status: str
    approval_decision_note: str


def meeting_summary_thread_config(workflow_id: int) -> dict[str, dict[str, str]]:
    """LangGraph ``configurable`` entry: stable thread id per ``Workflow`` row."""
    return {"configurable": {"thread_id": f"workflow-{int(workflow_id)}"}}


def graph_first_interrupt_value(result: Mapping[str, Any]) -> Any | None:
    """Extract the first ``interrupt(...)`` payload from an invoke result (if any)."""
    intr = result.get("__interrupt__")
    if not intr:
        return None
    first = intr[0]
    return getattr(first, "value", first)


def build_meeting_summary_graph(checkpointer: Any) -> CompiledStateGraph:
    """Compiled graph with ``wait_for_approval`` interrupt (requires a checkpointer)."""
    workflow = StateGraph(MeetingWorkflowState)
    workflow.add_node("generate_summary", _node_generate_summary)
    workflow.add_node("extract_action_items", _node_extract_action_items)
    workflow.add_node("wait_for_approval", _node_wait_for_approval)
    workflow.add_edge(START, "generate_summary")
    workflow.add_edge("generate_summary", "extract_action_items")
    workflow.add_edge("extract_action_items", "wait_for_approval")
    workflow.add_edge("wait_for_approval", END)
    return workflow.compile(checkpointer=checkpointer)


def invoke_meeting_summary_graph(
    *,
    notes: str,
    workflow_id: int,
    checkpoint_path: Path | str,
) -> MeetingWorkflowState:
    """Run summary + action items + interrupt; returns state (may include ``__interrupt__``)."""
    path = Path(checkpoint_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cfg = meeting_summary_thread_config(workflow_id)
    with SqliteSaver.from_conn_string(str(path)) as saver:
        compiled = build_meeting_summary_graph(saver)
        initial: MeetingWorkflowState = {"notes": notes}
        out = compiled.invoke(cast(MeetingWorkflowState, initial), cfg)
    return cast(MeetingWorkflowState, out)


def resume_meeting_summary_graph(
    *,
    workflow_id: int,
    resume_payload: dict[str, Any],
    checkpoint_path: Path | str,
) -> MeetingWorkflowState:
    """Resume after ``interrupt`` using the same SQLite checkpointer + thread id."""
    cfg = meeting_summary_thread_config(workflow_id)
    with SqliteSaver.from_conn_string(str(Path(checkpoint_path))) as saver:
        compiled = build_meeting_summary_graph(saver)
        out = compiled.invoke(Command(resume=resume_payload), cfg)
    return cast(MeetingWorkflowState, out)


def meeting_state_to_summary_output(state: MeetingWorkflowState) -> MeetingSummaryOutput:
    """Build API output from terminal graph state (approval must be completed)."""
    summary = str(state.get("summary") or "").strip()
    raw_items = state.get("action_items") or []
    items = [MeetingActionItem.model_validate(d) for d in raw_items]
    return MeetingSummaryOutput(summary=summary, action_items=items)


def run_meeting_summary_workflow(
    notes: str,
    *,
    graph: CompiledStateGraph | None = None,
    thread_id: str = "dev-meeting-summary",
    approval_resume: dict[str, Any] | None = None,
) -> MeetingSummaryOutput:
    """Invoke meeting-summary graph including human approval (defaults to auto-approve)."""
    mem = MemorySaver()
    compiled = graph or build_meeting_summary_graph(mem)
    cfg = {"configurable": {"thread_id": thread_id}}
    out = compiled.invoke(cast(MeetingWorkflowState, {"notes": notes}), cfg)
    if graph_first_interrupt_value(out) is not None:
        payload = approval_resume or {
            "action": _APPROVAL_ACTION_APPROVE,
            "note": "",
        }
        out = compiled.invoke(Command(resume=payload), cfg)
    if graph_first_interrupt_value(out) is not None:
        msg = "meeting summary graph is still interrupted after resume"
        raise RuntimeError(msg)

    return meeting_state_to_summary_output(cast(MeetingWorkflowState, out))


def _llm_summarize_notes(notes: str) -> str:
    msgs = [
        ChatMessage(
            role="system",
            content=prompt_template(PromptKey.MEETING_SUMMARY_SUMMARIZE_SYSTEM),
        ),
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
                {
                    "role": "system",
                    "content": prompt_template(PromptKey.MEETING_SUMMARY_ACTION_ITEMS_SYSTEM),
                },
                {"role": "user", "content": payload},
            ],
            temperature=0.1,
        ),
    )
    return list(extraction.action_items)


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


def _node_wait_for_approval(state: MeetingWorkflowState) -> MeetingWorkflowState:
    draft = {
        "summary": state.get("summary", ""),
        "action_items": state.get("action_items") or [],
    }
    decision = interrupt(draft)
    if not isinstance(decision, dict):
        msg = "approval resume payload must be a JSON object."
        raise TypeError(msg)

    action = str(decision.get("action") or "").strip().lower()
    note = str(decision.get("note") or "").strip()
    if action == _APPROVAL_ACTION_REJECT:
        return {"approval_status": _APPROVAL_RESULT_REJECTED, "approval_decision_note": note}
    if action != _APPROVAL_ACTION_APPROVE:
        unknown = decision.get("action")
        raise ValueError(f"unknown approval action: {unknown!r}")

    return {"approval_status": _APPROVAL_RESULT_APPROVED, "approval_decision_note": note}


__all__ = [
    "MeetingActionItem",
    "MeetingSummaryOutput",
    "MeetingWorkflowState",
    "build_meeting_summary_graph",
    "graph_first_interrupt_value",
    "invoke_meeting_summary_graph",
    "meeting_state_to_summary_output",
    "meeting_summary_thread_config",
    "resume_meeting_summary_graph",
    "run_meeting_summary_workflow",
]
