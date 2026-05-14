import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApprovalCard } from "../features/approvals/ApprovalCard";
import { WorkflowTimeline } from "../features/workflow/WorkflowTimeline";
import { fetchPendingApprovals, startMeetingSummaryWorkflow } from "../services/approvalsApi";
import { fetchMeetings } from "../services/meetingsApi";
import { fetchWorkflowList } from "../services/workflowsApi";
import type { WorkflowStatus } from "../types/workflows";

type TabKey = "run" | "approvals";

const WF_STATUS_ROW: Partial = {
  pending: "bg-slate-700 text-slate-300",
  processing: "bg-amber-500/20 text-amber-400",
  waiting_approval: "bg-blue-500/20 text-blue-300",
  completed: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-rose-500/20 text-rose-400",
  rejected: "bg-rose-500/20 text-rose-300",
};

const WF_STATUS_LABEL: Partial = {
  pending: "Pending",
  processing: "Processing",
  waiting_approval: "Awaiting approval",
  completed: "Completed",
  failed: "Failed",
  rejected: "Rejected",
};

export function MeetingSummaryPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<TabKey>("run");
  const [trackedId, setTrackedId] = useState<number | null>(null);
  const [selectedMeetingId, setSelectedMeetingId] = useState<number | "">("");
  const [runMessage, setRunMessage] = useState<string | null>(null);

  const pending = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: fetchPendingApprovals,
  });

  const meetings = useQuery({
    queryKey: ["meetings", "list"],
    queryFn: fetchMeetings,
  });

  const workflowsList = useQuery({
    queryKey: ["workflows", "list"],
    queryFn: () => fetchWorkflowList(40),
    enabled: tab === "run",
  });

  const startMut = useMutation({
    mutationFn: async (meetingId: number) => {
      const res = await startMeetingSummaryWorkflow(meetingId);
      return res.data;
    },
    onMutate: () => setRunMessage(null),
    onSuccess: async (data, variables) => {
      await queryClient.invalidateQueries({ queryKey: ["approvals", "pending"] });
      await queryClient.invalidateQueries({ queryKey: ["meetingAiSummary", variables] });
      await queryClient.invalidateQueries({ queryKey: ["workflows", "list"] });
      setTrackedId(data.workflow_id);
      setTab("approvals");
      setRunMessage("Workflow started. Review progress below or approve when the draft is ready.");
    },
    onError: (err: unknown) => setRunMessage(resolveWorkflowError(err)),
  });
  const meetingOptions = meetings.data ?? [];

  const pendingCount = pending.data?.length ?? 0;
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Meeting summary</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
          Run AI meeting summaries, track workflow progress, and approve or reject drafts before they are saved. After approval, open the meeting from Meetings to view the finalized read-only summary.
        </p>
      </div>

      <div className="flex w-full max-w-md gap-1 rounded-lg border border-slate-800 bg-slate-900/70 p-1">
        <button type="button" className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${tab === "run" ? "bg-slate-700 text-white shadow" : "text-slate-400 hover:text-slate-200"}`} onClick={() => setTab("run")}>
          Run &amp; track
        </button>
        <button
          type="button"
          className={`relative flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${tab === "approvals" ? "bg-slate-700 text-white shadow" : "text-slate-400 hover:text-slate-200"}`}
          onClick={() => setTab("approvals")}
        >
          Approvals
          {pendingCount > 0 ? <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-amber-500 px-1 text-[10px] font-bold text-emerald-950">{pendingCount}</span> : null}
        </button>
      </div>

      {tab === "run" ? (
        <>
          <section className="max-w-2xl rounded-xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-sm font-semibold text-slate-200">Generate summary</h2>
            <p className="mt-1 text-xs text-slate-500">Select a meeting to start an AI workflow.</p>

            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
              <select
                className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none disabled:opacity-50"
                disabled={meetings.status === "pending" || meetings.isFetching}
                value={selectedMeetingId === "" ? "" : String(selectedMeetingId)}
                onChange={(e) => {
                  const v = e.target.value;
                  setSelectedMeetingId(v === "" ? "" : Number(v));
                }}
              >
                <option value="">{meetings.status === "pending" ? "Loading meetings…" : "Select a meeting"}</option>
                {meetingOptions.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title} (#{m.id})
                  </option>
                ))}
              </select>
              <button
                className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                disabled={selectedMeetingId === "" || startMut.isPending}
                type="button"
                onClick={() => {
                  if (selectedMeetingId === "") {
                    return;
                  }
                  startMut.mutate(selectedMeetingId);
                }}
              >
                {startMut.isPending ? "Starting…" : "Run workflow"}
              </button>
            </div>

            {meetings.status === "error" ? <p className="mt-3 text-sm text-rose-400">We couldn’t load your meetings. Check your connection and try again.</p> : null}
            {runMessage ? <p className={`mt-3 text-sm ${runMessage.startsWith("Unable") ? "text-rose-400" : "text-emerald-400"}`}>{runMessage}</p> : null}
          </section>

          <section className="max-w-3xl rounded-xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-200">Your workflows</h2>
                <p className="mt-1 text-xs text-slate-500">Recent runs on your meetings — click a row to open the timeline below.</p>
              </div>
              <button className="text-xs font-medium text-emerald-400 hover:text-emerald-300 disabled:opacity-50" disabled={workflowsList.isFetching} type="button" onClick={() => void workflowsList.refetch()}>
                {workflowsList.isFetching ? "Refreshing…" : "Refresh"}
              </button>
            </div>

            {workflowsList.status === "pending" ? (
              <p className="mt-4 text-sm text-slate-500">Loading workflows…</p>
            ) : workflowsList.status === "error" ? (
              <p className="mt-4 text-sm text-rose-400">Unable to load workflow list.</p>
            ) : (workflowsList.data?.length ?? 0) === 0 ? (
              <p className="mt-4 rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-8 text-center text-sm text-slate-500">No workflows yet. Start one above.</p>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-900/90 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
                      <th className="px-3 py-2">ID</th>
                      <th className="px-3 py-2">Meeting</th>
                      <th className="px-3 py-2 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(workflowsList.data ?? []).map((row, idx) => (
                      <tr
                        key={row.id}
                        className={`cursor-pointer border-b border-slate-800/60 transition hover:bg-slate-800/40 ${trackedId === row.id ? "bg-slate-800/50" : idx % 2 === 1 ? "bg-slate-900/20" : ""}`}
                        tabIndex={0}
                        role="button"
                        onClick={() => setTrackedId(row.id)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            setTrackedId(row.id);
                          }
                        }}
                      >
                        <td className="px-3 py-2.5 font-mono text-xs text-slate-400">{row.id}</td>
                        <td className="max-w-[14rem] px-3 py-2.5 md:max-w-xl">
                          <span className="block truncate font-medium text-slate-100">{row.meeting_title}</span>
                          <span className="text-[11px] text-slate-600">Meeting #{row.meeting_id}</span>
                        </td>
                        <td className="px-3 py-2.5 text-right align-middle whitespace-nowrap">
                          <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${WF_STATUS_ROW[row.status] ?? "bg-slate-700 text-slate-300"}`}>{WF_STATUS_LABEL[row.status] ?? row.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {trackedId !== null ? (
            <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <h2 className="text-sm font-semibold text-slate-200">Workflow status</h2>
                <button className="text-xs font-medium text-slate-500 hover:text-slate-400" type="button" onClick={() => setTrackedId(null)}>
                  Dismiss
                </button>
              </div>
              <WorkflowTimeline workflowId={trackedId} poll />
            </section>
          ) : null}
        </>
      ) : null}

      {tab === "approvals" ? (
        <section className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Pending drafts</h2>
              <p className="text-xs text-slate-500">Summaries awaiting your decision appear here.</p>
            </div>
            <button type="button" className="text-xs font-medium text-emerald-400 hover:text-emerald-300 disabled:opacity-50" disabled={pending.isFetching} onClick={() => void pending.refetch()}>
              {pending.isFetching ? "Refreshing…" : "Refresh"}
            </button>
          </div>

          {pending.status === "pending" ? <p className="text-sm text-slate-500">Loading approvals…</p> : null}
          {pending.status === "error" ? <p className="text-sm text-rose-400">Unable to fetch pending approvals.</p> : null}

          {(pending.data?.length ?? 0) === 0 && pending.status === "success" ? (
            <p className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-8 text-center text-sm text-slate-500">
              Nothing is waiting on you right now. Start a workflow in the Run &amp; track tab when you&apos;re ready.
            </p>
          ) : null}

          <div className="grid gap-6 lg:grid-cols-2">
            {(pending.data ?? []).map((a) => (
              <ApprovalCard key={a.id} approval={a} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function resolveWorkflowError(err: unknown): string {
  if (typeof err === "object" && err !== null && "response" in err) {
    const r = err as { response?: { data?: unknown } };
    const d = r.response?.data;
    if (typeof d === "object" && d !== null) {
      if ("meeting_id" in d || "detail" in d) {
        const detail = (d as { detail?: unknown }).detail;
        const meetingErrors = (d as { meeting_id?: unknown }).meeting_id;
        if (Array.isArray(meetingErrors)) {
          return String(meetingErrors[0]);
        }
        if (typeof detail === "string") {
          return detail;
        }
      }
    }
  }
  return "Unable to start the workflow.";
}
