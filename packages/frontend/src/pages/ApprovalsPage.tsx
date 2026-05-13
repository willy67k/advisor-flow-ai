import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApprovalCard } from "../features/approvals/ApprovalCard.tsx";
import { fetchPendingApprovals, startMeetingSummaryWorkflow } from "../services/approvalsApi.ts";
import { fetchMeetings } from "../services/meetingsApi.ts";

export function ApprovalsPage() {
  const queryClient = useQueryClient();
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

  const startMut = useMutation({
    mutationFn: async (meetingId: number) => {
      await startMeetingSummaryWorkflow(meetingId);
    },
    onMutate: () => setRunMessage(null),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["approvals", "pending"] });
      setRunMessage("Check pending drafts below — tap Refresh if the card hasn’t appeared yet.");
    },
    onError: (err: unknown) => setRunMessage(resolveWorkflowError(err)),
  });

  const meetingOptions = meetings.data ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Approvals</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">Choose a meeting, generate an AI summary, then approve or reject the draft before it is saved for your records.</p>
      </div>

      <section className="max-w-2xl rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="text-sm font-semibold text-slate-200">Generate summary</h2>
        <p className="mt-1 text-xs text-slate-500">Select a meeting to produce a draft for review.</p>

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
            {startMut.isPending ? "Starting…" : "Generate summary"}
          </button>
        </div>

        {meetings.status === "error" ? <p className="mt-3 text-sm text-rose-400">We couldn’t load your meetings. Check your connection and try again.</p> : null}
        {runMessage ? <p className="mt-3 text-sm text-emerald-400">{runMessage}</p> : null}
      </section>

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
          <p className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-8 text-center text-sm text-slate-500">Nothing is waiting on you yet. Generate a summary above or check back later.</p>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-2">
          {(pending.data ?? []).map((a) => (
            <ApprovalCard key={a.id} approval={a} />
          ))}
        </div>
      </section>
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
  return "Unable to generate the summary.";
}
