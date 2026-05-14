import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { useClients } from "../hooks/useClients";
import { fetchMeeting, fetchMeetingAiSummary } from "../services/meetingsApi";

function statusLabel(status: string | null): string {
  if (!status) return "—";
  const map: Record = {
    pending: "Pending",
    processing: "Processing",
    waiting_approval: "Awaiting approval",
    completed: "Completed",
    failed: "Failed",
    rejected: "Rejected",
  };
  return map[status] ?? status;
}

export function MeetingDetailPage() {
  const { meetingId: idParam } = useParams<{ meetingId: string }>();
  const meetingId = idParam ? parseInt(idParam, 10) : NaN;
  const validId = !isNaN(meetingId) && meetingId > 0;

  const { data: clients } = useClients();

  const meetingQuery = useQuery({
    queryKey: ["meetings", "detail", meetingId],
    queryFn: () => fetchMeeting(meetingId),
    enabled: validId,
  });

  const summaryQuery = useQuery({
    queryKey: ["meetingAiSummary", meetingId],
    queryFn: () => fetchMeetingAiSummary(meetingId),
    enabled: validId,
    refetchInterval: (q) => {
      const d = q.state.data;
      if (!d?.workflow_status) return false;
      if (d.has_approved_summary) return false;
      if (d.workflow_status === "failed" || d.workflow_status === "rejected") return false;
      return 5000;
    },
  });

  if (!validId) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-rose-400">Invalid meeting id.</p>
        <Link className="text-sm font-medium text-emerald-400 hover:text-emerald-300" to="/meetings">
          Back to meetings
        </Link>
      </div>
    );
  }

  const meeting = meetingQuery.data;
  const ai = summaryQuery.data;
  const clientName = meeting ? (clients ?? []).find((c) => c.id === meeting.client)?.name : undefined;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link className="text-xs font-medium text-slate-500 hover:text-emerald-400" to="/meetings">
            ← Meetings
          </Link>
          {meetingQuery.status === "success" && meeting ? (
            <>
              <h1 className="mt-2 text-xl font-semibold tracking-tight text-white">{meeting.title}</h1>
              <p className="mt-1 text-sm text-slate-400">
                {meeting.date}
                {clientName ? ` · ${clientName}` : ""}
              </p>
            </>
          ) : meetingQuery.status === "pending" ? (
            <p className="mt-3 text-sm text-slate-500">Loading meeting…</p>
          ) : meetingQuery.status === "error" ? (
            <p className="mt-3 text-sm text-rose-400">Unable to load this meeting.</p>
          ) : null}
        </div>
      </div>

      {meetingQuery.status === "success" && meeting ? (
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-sm font-semibold text-slate-200">Meeting notes</h2>
          <p className="mt-3 text-sm leading-relaxed whitespace-pre-wrap text-slate-300">{meeting.notes.trim() ? meeting.notes : "No notes recorded."}</p>
        </section>
      ) : null}

      <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Approved AI summary</h2>
            <p className="mt-1 text-xs text-slate-500">Final output after workflow completion and approval. Read-only reference.</p>
          </div>
          {summaryQuery.status === "success" && ai?.workflow_status ? <span className="rounded-full border border-slate-700 px-3 py-1 text-xs font-medium text-slate-400">Workflow: {statusLabel(ai.workflow_status)}</span> : null}
        </div>

        {summaryQuery.status === "pending" ? (
          <p className="text-sm text-slate-500">Loading summary status…</p>
        ) : summaryQuery.status === "error" ? (
          <p className="text-sm text-rose-400">Could not load summary information.</p>
        ) : !ai?.workflow_id ? (
          <p className="text-sm text-slate-500">
            No workflow has been run for this meeting yet.{" "}
            <Link className="font-medium text-emerald-400 hover:text-emerald-300" to="/meeting-summary">
              Start one from Meeting summary
            </Link>
            .
          </p>
        ) : ai.has_approved_summary && ai.summary ? (
          <>
            <div>
              <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Summary</h3>
              <p className="mt-2 text-sm leading-relaxed whitespace-pre-wrap text-slate-200">{ai.summary}</p>
            </div>
            {ai.action_items.length > 0 ? (
              <div>
                <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Action items</h3>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-slate-300">
                  {ai.action_items.map((it, idx) => (
                    <li key={`${it.task}-${idx}`}>
                      <span className="font-medium text-slate-100">{it.task}</span>
                      {(it.owner || it.due) && <span className="mt-1 block text-xs text-slate-500">{[it.owner ? `Owner: ${it.owner}` : null, it.due ? `Due: ${it.due}` : null].filter(Boolean).join(" · ")}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {(ai.approval_decision_note ?? "").trim() ? (
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-3">
                <p className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Approval note</p>
                <p className="mt-2 text-sm whitespace-pre-wrap text-slate-400">{ai.approval_decision_note}</p>
              </div>
            ) : null}
          </>
        ) : (
          <div className="space-y-3 text-sm text-slate-400">
            <p>
              A workflow is linked to this meeting, but there is no approved summary visible here yet (<span className="font-medium text-slate-300">{statusLabel(ai.workflow_status)}</span>).
            </p>
            {(ai.workflow_status === "waiting_approval" || (ai.pending_approval_id ?? 0) > 0 || ai.workflow_status === "processing") && (
              <p>
                <Link className="font-medium text-emerald-400 hover:text-emerald-300" to="/meeting-summary">
                  Open Meeting summary
                </Link>{" "}
                {ai.workflow_status === "waiting_approval" ? "to review and approve the draft." : "to monitor progress."}
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
