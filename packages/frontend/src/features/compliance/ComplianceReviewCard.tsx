import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { clearComplianceHold, rejectComplianceHold } from "../../services/complianceApi";
import type { CompliancePendingItem } from "../../types/compliance";

type Props = {
  readonly item: CompliancePendingItem;
};

function riskBadgeClass(level: string | undefined): string {
  if (level === "high") return "bg-rose-500/20 text-rose-200 border-rose-500/40";
  if (level === "medium") return "bg-amber-500/20 text-amber-200 border-amber-500/40";
  return "bg-slate-600/40 text-slate-300 border-slate-600";
}

export function ComplianceReviewCard({ item }: Props) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const payload = item.compliance_review;
  const report = payload.compliance;
  const risk = report?.risk_level;

  const invalidate = async () => {
    await Promise.all([queryClient.invalidateQueries({ queryKey: ["compliance", "pending"] }), queryClient.invalidateQueries({ queryKey: ["workflows", "list"] }), queryClient.invalidateQueries({ queryKey: ["approvals", "pending"] })]);
  };

  const clearMut = useMutation({
    mutationFn: () => clearComplianceHold(item.workflow_id, note.trim()),
    onMutate: () => setFeedback(null),
    onSuccess: async () => {
      await invalidate();
      setNote("");
      setFeedback("Cleared. The advisor can now review and approve the draft.");
    },
    onError: (err: unknown) => setFeedback(resolveErr(err)),
  });

  const rejectMut = useMutation({
    mutationFn: () => rejectComplianceHold(item.workflow_id, note.trim()),
    onMutate: () => setFeedback(null),
    onSuccess: async () => {
      await invalidate();
      setNote("");
      setFeedback("Rejected. The workflow is closed at compliance; the advisor will see this on the meeting.");
    },
    onError: (err: unknown) => setFeedback(resolveErr(err)),
  });

  const busy = clearMut.isPending || rejectMut.isPending;
  const items = [...(payload.action_items ?? [])];

  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="min-w-0">
          <p className="text-[11px] tracking-wide text-slate-500 uppercase">High-risk draft · Workflow #{item.workflow_id}</p>
          <h2 className="mt-1 truncate text-base font-semibold text-slate-100">{item.meeting_title}</h2>
          <p className="mt-0.5 text-xs text-slate-500">Meeting #{item.meeting_id}</p>
        </div>
        {risk ? <span className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase ${riskBadgeClass(risk)}`}>{risk} risk</span> : null}
      </header>

      <div className="mt-4 space-y-4">
        {report?.findings?.length ? (
          <section>
            <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Findings</h3>
            <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm text-amber-100/90">
              {report.findings.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <section>
          <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Draft summary</h3>
          <p className="mt-2 text-sm leading-relaxed whitespace-pre-wrap text-slate-300">{payload.summary?.trim() ? payload.summary : "—"}</p>
        </section>

        {items.length > 0 ? (
          <section>
            <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">Action items</h3>
            <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-slate-300">
              {items.map((it, idx) => (
                <li key={`${item.workflow_id}-${idx}-${it.task}`}>
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
            className="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 focus:outline-none disabled:opacity-50"
            disabled={busy}
            placeholder="Internal note for the audit trail…"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>

        {feedback ? <p className={`text-sm ${feedback.startsWith("Cleared") ? "text-emerald-400" : feedback.startsWith("Rejected") ? "text-slate-300" : "text-rose-400"}`}>{feedback}</p> : null}

        <div className="flex flex-wrap gap-3">
          <button className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50" disabled={busy} type="button" onClick={() => clearMut.mutate()}>
            {clearMut.isPending ? "Clearing…" : "Clear for advisor review"}
          </button>
          <button
            className="rounded-lg border border-rose-500/50 bg-transparent px-4 py-2 text-sm font-medium text-rose-200 hover:bg-rose-950/50 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy}
            type="button"
            onClick={() => rejectMut.mutate()}
          >
            {rejectMut.isPending ? "Rejecting…" : "Reject at compliance"}
          </button>
        </div>
      </div>
    </article>
  );
}

function resolveErr(err: unknown): string {
  if (typeof err === "object" && err !== null && "response" in err) {
    const r = err as { response?: { data?: unknown } };
    const d = r.response?.data;
    if (typeof d === "object" && d !== null && "detail" in d) {
      const detail = (d as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
  }
  return "Something went wrong. Try again.";
}
