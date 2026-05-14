"""Meeting summary LangGraph workflow (Step 3.2 + 4.1 interrupt)."""

from unittest.mock import patch

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.services.workflows.meeting_summary import (
    MeetingActionItem,
    MeetingSummaryOutput,
    build_meeting_summary_graph,
    graph_first_interrupt_value,
    run_meeting_summary_workflow,
)

SAMPLE_NOTES = (
    "Client reviewed Q2 portfolio drift. Discussed increasing fixed income vs equity. "
    "Jane to send IPS draft by Friday. Advisor schedules follow-up in two weeks."
)


@pytest.mark.django_db
def test_run_meeting_summary_workflow_returns_structured_output():
    patched_items = [
        MeetingActionItem(task="Send IPS draft", owner="Jane", due="Friday"),
        MeetingActionItem(task="Schedule follow-up meeting", owner="Advisor", due="two weeks"),
    ]

    with (
        patch(
            "app.services.workflows.meeting_summary._llm_summarize_notes",
            return_value="Portfolio drift reviewed; IPS update planned.",
        ),
        patch(
            "app.services.workflows.meeting_summary._llm_extract_action_items",
            return_value=patched_items,
        ),
    ):
        out = run_meeting_summary_workflow(SAMPLE_NOTES)

    assert isinstance(out, MeetingSummaryOutput)
    assert out.summary == "Portfolio drift reviewed; IPS update planned."
    assert len(out.action_items) == 2
    assert out.action_items[0].task.startswith("Send IPS")


@pytest.mark.django_db
def test_meeting_summary_graph_invokes_ordered_nodes():
    calls: dict[str, int] = {"summary": 0, "extract": 0}

    def track_summary(*, notes: str, rag_context: str = "") -> str:
        calls["summary"] += 1
        assert "Q2 portfolio" in notes
        assert isinstance(rag_context, str)
        return "s"

    def track_extract(*, notes: str, summary: str) -> list[MeetingActionItem]:
        calls["extract"] += 1
        assert summary == "s"
        assert notes
        return [MeetingActionItem(task="Do something")]

    with (
        patch(
            "app.services.workflows.meeting_summary._llm_summarize_notes",
            side_effect=track_summary,
        ),
        patch(
            "app.services.workflows.meeting_summary._llm_extract_action_items",
            side_effect=track_extract,
        ),
    ):
        mem = MemorySaver()
        graph = build_meeting_summary_graph(mem)
        cfg = {"configurable": {"thread_id": "ordered-nodes-test"}}
        halted = graph.invoke({"notes": SAMPLE_NOTES}, cfg)
        assert graph_first_interrupt_value(halted) is not None
        final = graph.invoke(Command(resume={"action": "approve", "note": ""}), cfg)
        assert graph_first_interrupt_value(final) is None

    assert calls["summary"] == calls["extract"] == 1
    assert final["summary"] == "s"
    assert final["action_items"] == [{"task": "Do something", "owner": None, "due": None}]
    assert final.get("approval_status") == "approved"


@pytest.mark.django_db
def test_empty_notes_skips_downstream_extract_llm():
    captured: dict[str, bool] = {"extract_called": False}

    def boom(*_args: object, **_kwargs: object) -> list[MeetingActionItem]:
        captured["extract_called"] = True
        raise AssertionError("_llm_extract_action_items must not run for empty summaries")

    with (
        patch("app.services.workflows.meeting_summary._llm_summarize_notes"),
        patch(
            "app.services.workflows.meeting_summary._llm_extract_action_items",
            side_effect=boom,
        ),
    ):
        out = run_meeting_summary_workflow("   \n")

    assert not captured["extract_called"]
    assert out.summary == ""
    assert out.action_items == []
