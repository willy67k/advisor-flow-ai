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
from app.models.meeting import Meeting
from app.prompts import PromptKey, prompt_template
from app.services.ai.gateway import ChatMessage, LLMProvider, complete_chat
from app.services.ai.retrieval import retrieve_context_for_meeting_notes
from app.services.compliance.reviewer import review_meeting_summary_draft

logger = logging.getLogger(__name__)

_APPROVAL_ACTION_APPROVE = "approve"
_APPROVAL_ACTION_REJECT = "reject"

_APPROVAL_RESULT_APPROVED = "approved"
_APPROVAL_RESULT_REJECTED = "rejected"

_COMPLIANCE_ACTION_CLEAR = "clear"
_COMPLIANCE_ACTION_REJECT = "reject"

_COMPLIANCE_ROUTER_HOLD = "compliance_hold"
_COMPLIANCE_ROUTER_ADVISOR = "advisor_gate"
_COMPLIANCE_ROUTER_END = "stop"

_HIGH_RISK = "high"

_NOTES_PLACEHOLDER_FOR_RAG_ONLY = (
    "(No typed meeting notes in the app — summarize substantively from the document excerpts.)"
)


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
    meeting_id: int
    rag_context: str
    summary: str
    action_items: list[dict[str, Any]]
    compliance_risk: str
    compliance_report: dict[str, Any]
    compliance_decision: str
    compliance_decision_note: str
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
    """Compiled graph: RAG → summary → compliance → optional compliance hold → advisor approval."""
    workflow = StateGraph(MeetingWorkflowState)
    workflow.add_node("retrieve_context", _node_retrieve_context)
    workflow.add_node("generate_summary", _node_generate_summary)
    workflow.add_node("extract_action_items", _node_extract_action_items)
    workflow.add_node("compliance_check", _node_compliance_check)
    workflow.add_node("wait_for_compliance", _node_wait_for_compliance)
    workflow.add_node("wait_for_advisor_approval", _node_wait_for_advisor_approval)
    workflow.add_edge(START, "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_summary")
    workflow.add_edge("generate_summary", "extract_action_items")
    workflow.add_edge("extract_action_items", "compliance_check")
    workflow.add_conditional_edges(
        "compliance_check",
        _route_after_compliance_check,
        {
            _COMPLIANCE_ROUTER_HOLD: "wait_for_compliance",
            _COMPLIANCE_ROUTER_ADVISOR: "wait_for_advisor_approval",
        },
    )
    workflow.add_conditional_edges(
        "wait_for_compliance",
        _route_after_compliance_resume,
        {
            _COMPLIANCE_ROUTER_ADVISOR: "wait_for_advisor_approval",
            _COMPLIANCE_ROUTER_END: END,
        },
    )
    workflow.add_edge("wait_for_advisor_approval", END)
    return workflow.compile(checkpointer=checkpointer)


def invoke_meeting_summary_graph(
    *,
    notes: str,
    workflow_id: int,
    checkpoint_path: Path | str,
    meeting_id: int | None = None,
) -> MeetingWorkflowState:
    """Run retrieval + summary + action items + interrupt (may include ``__interrupt__``)."""
    path = Path(checkpoint_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cfg = meeting_summary_thread_config(workflow_id)
    with SqliteSaver.from_conn_string(str(path)) as saver:
        compiled = build_meeting_summary_graph(saver)
        initial = cast(
            MeetingWorkflowState,
            {
                "notes": notes,
                **({"meeting_id": int(meeting_id)} if meeting_id is not None else {}),
            },
        )
        out = compiled.invoke(initial, cfg)
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
    meeting_id: int | None = None,
) -> MeetingSummaryOutput:
    """Invoke meeting-summary graph including human approval (defaults to auto-approve)."""
    mem = MemorySaver()
    compiled = graph or build_meeting_summary_graph(mem)
    cfg = {"configurable": {"thread_id": thread_id}}
    initial = cast(
        MeetingWorkflowState,
        {"notes": notes, **({"meeting_id": int(meeting_id)} if meeting_id is not None else {})},
    )
    out = compiled.invoke(initial, cfg)
    while graph_first_interrupt_value(out) is not None:
        intr = graph_first_interrupt_value(out)
        if isinstance(intr, dict) and intr.get("stage") == "compliance_review":
            payload = {"action": _COMPLIANCE_ACTION_CLEAR, "note": ""}
        else:
            payload = approval_resume or {
                "action": _APPROVAL_ACTION_APPROVE,
                "note": "",
            }
        out = compiled.invoke(Command(resume=payload), cfg)
    if graph_first_interrupt_value(out) is not None:
        msg = "meeting summary graph is still interrupted after resume"
        raise RuntimeError(msg)

    return meeting_state_to_summary_output(cast(MeetingWorkflowState, out))


def _llm_summarize_notes(*, notes: str, rag_context: str = "") -> str:
    rc = rag_context.strip()
    if rc:
        user_blob = (
            "Use DOCUMENT EXCERPTS as factual context when relevant. "
            "If they contradict shorthand NOTES, prefer the excerpts for facts "
            "(names, numbers, timelines). Ignore irrelevant excerpts.\n\n"
            "DOCUMENT EXCERPTS:\n"
            f"{rc}\n\n"
            "---\nMEETING NOTES:\n"
            f"{notes}\n\n"
            "Write the summary only."
        )
    else:
        user_blob = f"Meeting notes:\n\n{notes}\n\nWrite the summary only."
    msgs = [
        ChatMessage(
            role="system",
            content=prompt_template(PromptKey.MEETING_SUMMARY_SUMMARIZE_SYSTEM),
        ),
        ChatMessage(
            role="user",
            content=user_blob,
        ),
    ]
    result = complete_chat(
        msgs,
        provider=LLMProvider.OPENAI,
        temperature=0.2,
        observability_prompt_key=PromptKey.MEETING_SUMMARY_SUMMARIZE_SYSTEM,
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


def _node_retrieve_context(state: MeetingWorkflowState) -> MeetingWorkflowState:
    mid = state.get("meeting_id")
    notes = str(state.get("notes") or "")
    if mid is None:
        return {"rag_context": ""}
    row = Meeting.objects.filter(pk=int(mid)).only("advisor_id").first()
    if row is None:
        return {"rag_context": ""}
    rag = retrieve_context_for_meeting_notes(
        meeting_id=int(mid),
        scoped_advisor_id=int(row.advisor_id),
        query_text=notes,
    )
    return {"rag_context": rag}


def _node_generate_summary(state: MeetingWorkflowState) -> MeetingWorkflowState:
    notes = state.get("notes", "").strip()
    rag = str(state.get("rag_context") or "").strip()
    if not notes and not rag:
        logger.warning(
            "meeting_summary: empty notes and no document context; skipping LLM summarize."
        )
        return {"summary": ""}
    effective_notes = notes if notes else _NOTES_PLACEHOLDER_FOR_RAG_ONLY
    summary = _llm_summarize_notes(notes=effective_notes, rag_context=rag)
    return {"summary": summary}


def _node_extract_action_items(state: MeetingWorkflowState) -> MeetingWorkflowState:
    notes_raw = str(state.get("notes") or "").strip()
    summary = state.get("summary", "")
    if not summary.strip():
        return {"action_items": []}

    rag = str(state.get("rag_context") or "").strip()
    notes_for_extract = notes_raw or _NOTES_PLACEHOLDER_FOR_RAG_ONLY
    notes = (
        notes_for_extract + "\n\n[Retrieved excerpts from uploaded documents]\n" + rag
        if rag
        else notes_for_extract
    )

    raw_items = _llm_extract_action_items(notes=notes, summary=summary)
    return {"action_items": [item.model_dump() for item in raw_items]}


def _node_compliance_check(state: MeetingWorkflowState) -> MeetingWorkflowState:
    summary = str(state.get("summary") or "")
    items = state.get("action_items") or []
    if not summary.strip() and not items:
        report = review_meeting_summary_draft(summary="", action_items=[]).to_dict()
        return {
            "compliance_risk": report["risk_level"],
            "compliance_report": report,
        }
    raw_items: list[dict[str, Any]] = items if isinstance(items, list) else []
    result = review_meeting_summary_draft(summary=summary, action_items=raw_items)
    report = result.to_dict()
    return {
        "compliance_risk": result.risk_level.value,
        "compliance_report": report,
    }


def _route_after_compliance_check(state: MeetingWorkflowState) -> str:
    risk = str(state.get("compliance_risk") or "")
    return _COMPLIANCE_ROUTER_HOLD if risk == _HIGH_RISK else _COMPLIANCE_ROUTER_ADVISOR


def _node_wait_for_compliance(state: MeetingWorkflowState) -> MeetingWorkflowState:
    payload = {
        "stage": "compliance_review",
        "summary": state.get("summary", ""),
        "action_items": state.get("action_items") or [],
        "compliance": state.get("compliance_report") or {},
    }
    decision = interrupt(payload)
    if not isinstance(decision, dict):
        msg = "compliance resume payload must be a JSON object."
        raise TypeError(msg)

    action = str(decision.get("action") or "").strip().lower()
    note = str(decision.get("note") or "").strip()
    if action == _COMPLIANCE_ACTION_REJECT:
        return {"compliance_decision": "rejected", "compliance_decision_note": note}
    if action != _COMPLIANCE_ACTION_CLEAR:
        unknown = decision.get("action")
        raise ValueError(f"unknown compliance action: {unknown!r}")

    return {"compliance_decision": "cleared", "compliance_decision_note": note}


def _route_after_compliance_resume(state: MeetingWorkflowState) -> str:
    return (
        _COMPLIANCE_ROUTER_END
        if str(state.get("compliance_decision") or "") == "rejected"
        else _COMPLIANCE_ROUTER_ADVISOR
    )


def _node_wait_for_advisor_approval(state: MeetingWorkflowState) -> MeetingWorkflowState:
    draft = {
        "stage": "advisor_approval",
        "summary": state.get("summary", ""),
        "action_items": state.get("action_items") or [],
        "compliance": state.get("compliance_report") or {},
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
