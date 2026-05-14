import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { approveApproval, rejectApproval } from "../../services/approvalsApi.ts";
import type { PendingApproval } from "../../types/approvals.ts";

type Props = {
  readonly approval: PendingApproval;
};

export function ApprovalCard({ approval }: Props) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["approvals", "pending"] }),
      queryClient.invalidateQueries({ queryKey: ["meetingAiSummary", approval.meeting_id] }),
      queryClient.invalidateQueries({ queryKey: ["workflows", "list"] }),
    ]);
  };

  const approveMut = useMutation({
    mutationFn: () => approveApproval(approval.id, note.trim()),
    onMutate: () => setFeedback(null),
    onSuccess: async () => {
      await invalidate();
      setNote("");
      setFeedback("Approved. Your summary has been finalized.");
    },
    onError: (err: unknown) => setFeedback(resolveError(err)),
  });

  const rejectMut = useMutation({
    mutationFn: () => rejectApproval(approval.id, note.trim()),
    onMutate: () => setFeedback(null),
    onSuccess: async () => {
      await invalidate();
      setNote("");
      setFeedback("Rejected. This draft has been discarded.");
    },
    onError: (err: unknown) => setFeedback(resolveError(err)),
  });

  const busy = approveMut.isPending || rejectMut.isPending;

  const items = [...(approval.ai_draft_json.action_items ?? [])];

  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="min-w-0">
          <p className="text-[11px] tracking-wide text-slate-500 uppercase">Meeting summary draft</p>
          <h2 className="mt-1 truncate text-base font-semibold text-slate-100">{approval.meeting_title}</h2>
        </div>
      </header>

      <div className="mt-4 space-y-4">
        <section>
          <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Summary</h3>
          <p className="mt-2 text-sm leading-relaxed whitespace-pre-wrap text-slate-300">{approval.ai_draft_json.summary.trim() ? approval.ai_draft_json.summary : "—"}</p>
        </section>

        {items.length > 0 ? (
          <section>
            <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Action items</h3>
            <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-slate-300">
              {items.map((it, idx) => (
                <li key={`${approval.id}-${idx}-${it.task}`}>
                  <span className="font-medium text-slate-200">{it.task}</span>
                  {(it.owner || it.due) && <span className="mt-1 block text-xs text-slate-500">{[it.owner ? `Owner: ${it.owner}` : null, it.due ? `Due: ${it.due}` : null].filter(Boolean).join(" · ")}</span>}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <label className="block">
          <span className="text-xs font-medium text-slate-400">Decision note (optional)</span>
          <textarea
            className="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none disabled:opacity-50"
            disabled={busy}
            placeholder="Brief note for the record…"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>

        {feedback ? <p className={`text-sm ${feedback.startsWith("Approve") ? "text-emerald-400" : feedback.startsWith("Reject") ? "text-slate-300" : "text-rose-400"}`}>{feedback}</p> : null}

        <div className="flex flex-wrap gap-3">
          <button className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50" disabled={busy} type="button" onClick={() => approveMut.mutate()}>
            {approveMut.isPending ? "Approving…" : "Approve"}
          </button>
          <button
            className="rounded-lg border border-slate-600 bg-transparent px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy}
            type="button"
            onClick={() => rejectMut.mutate()}
          >
            {rejectMut.isPending ? "Rejecting…" : "Reject"}
          </button>
        </div>
      </div>
    </article>
  );
}

function resolveError(err: unknown): string {
  if (typeof err === "object" && err !== null && "response" in err) {
    const r = err as { response?: { data?: unknown } };
    const d = r.response?.data;
    if (typeof d === "object" && d !== null && "detail" in d) {
      const detail = (d as { detail: unknown }).detail;
      if (typeof detail === "string") {
        return detail;
      }
    }
  }
  return "Something went wrong. Try again.";
}
