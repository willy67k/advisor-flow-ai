import { useQuery } from "@tanstack/react-query";

import { ComplianceReviewCard } from "../features/compliance/ComplianceReviewCard";
import { fetchCompliancePending } from "../services/complianceApi";

export function ComplianceReviewsPage() {
  const pending = useQuery({
    queryKey: ["compliance", "pending"],
    queryFn: fetchCompliancePending,
    refetchInterval: (q) => ((q.state.data?.length ?? 0) > 0 ? 3000 : 12000),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Compliance reviews</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
          High-risk AI meeting summaries are held here until compliance clears or rejects them. Clearing releases the draft to the advisor for final approval; rejecting closes the workflow with a compliance outcome the advisor can see on
          the meeting record.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="text-xs text-slate-500">{pending.isFetching ? "Refreshing…" : pending.data ? `${pending.data.length} in queue` : ""}</p>
        <button className="text-xs font-medium text-violet-400 hover:text-violet-300 disabled:opacity-50" disabled={pending.isFetching} type="button" onClick={() => void pending.refetch()}>
          Refresh now
        </button>
      </div>

      {pending.status === "pending" ? <p className="text-sm text-slate-500">Loading queue…</p> : null}
      {pending.status === "error" ? <p className="text-sm text-rose-400">Unable to load compliance queue. Check permissions or try again.</p> : null}

      {pending.status === "success" && (pending.data?.length ?? 0) === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-10 text-center text-sm text-slate-500">
          No drafts are waiting on compliance. When an advisor runs a workflow that scores as high risk, it will appear here.
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        {(pending.data ?? []).map((row) => (
          <ComplianceReviewCard key={row.workflow_id} item={row} />
        ))}
      </div>
    </div>
  );
}
