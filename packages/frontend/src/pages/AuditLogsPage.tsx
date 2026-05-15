import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { fetchAuditLogs } from "../services/auditLogsApi";

function jsonSnippet(value: Record<string, unknown> | null): string {
  if (value == null) return "—";
  try {
    const s = JSON.stringify(value, null, 0);
    return s.length > 160 ? `${s.slice(0, 157)}…` : s;
  } catch {
    return "—";
  }
}

export function AuditLogsPage() {
  const [page, setPage] = useState(1);
  const [draftResourceType, setDraftResourceType] = useState("");
  const [draftResourceId, setDraftResourceId] = useState("");
  /** `null` = user has not run a search yet; otherwise snapshot used for the active query. */
  const [applied, setApplied] = useState<{ readonly resourceType?: string; readonly resourceId?: string } | null>(null);
  /** Bumped on each Search so identical filters still refetch when the user clicks Search again. */
  const [searchEpoch, setSearchEpoch] = useState(0);

  const logs = useQuery({
    queryKey: ["audit-logs", searchEpoch, page, applied?.resourceType ?? "", applied?.resourceId ?? ""],
    queryFn: () =>
      fetchAuditLogs(page, {
        resourceType: applied?.resourceType,
        resourceId: applied?.resourceId,
      }),
    enabled: applied !== null,
  });

  function handleSearch() {
    setPage(1);
    const rt = draftResourceType.trim();
    const rid = draftResourceId.trim();
    setApplied({
      resourceType: rt || undefined,
      resourceId: rid || undefined,
    });
    setSearchEpoch((n) => n + 1);
  }

  const pageSize = 25;
  const totalPages = logs.data ? Math.max(1, Math.ceil(logs.data.count / pageSize)) : 1;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Audit logs</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
          Immutable workflow and approval events (who acted, before/after snapshots). Visible only to workspace managers. Resource type uses substring match; click Search to query (typing alone does not fetch).
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Resource type
          <input
            className="w-40 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100 placeholder:text-slate-600"
            placeholder="workflow"
            type="text"
            value={draftResourceType}
            onChange={(e) => setDraftResourceType(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Resource ID
          <input
            className="w-40 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100 placeholder:text-slate-600"
            placeholder="42"
            type="text"
            value={draftResourceId}
            onChange={(e) => setDraftResourceId(e.target.value)}
          />
        </label>
        <button className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50" disabled={logs.isFetching} type="button" onClick={() => handleSearch()}>
          Search
        </button>
      </div>

      {applied === null ? <p className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-10 text-center text-sm text-slate-500">Adjust filters if needed, then click Search to load audit logs.</p> : null}

      {applied !== null && logs.status === "pending" ? <p className="text-sm text-slate-500">Loading…</p> : null}
      {applied !== null && logs.status === "error" ? <p className="text-sm text-rose-400">Unable to load audit logs.</p> : null}

      {applied !== null && logs.status === "success" ? (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
              <thead className="bg-slate-900/80 text-xs tracking-wide text-slate-400 uppercase">
                <tr>
                  <th className="px-3 py-2 font-medium whitespace-nowrap">Time</th>
                  <th className="px-3 py-2 font-medium whitespace-nowrap">Action</th>
                  <th className="px-3 py-2 font-medium whitespace-nowrap">Actor</th>
                  <th className="px-3 py-2 font-medium whitespace-nowrap">Resource</th>
                  <th className="min-w-[12rem] px-3 py-2 font-medium">Before</th>
                  <th className="min-w-[12rem] px-3 py-2 font-medium">After</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-200">
                {(logs.data.results ?? []).map((row) => (
                  <tr key={row.id} className="bg-slate-950/40 hover:bg-slate-900/60">
                    <td className="px-3 py-2 align-top text-xs whitespace-nowrap text-slate-400">{new Date(row.created_at).toLocaleString()}</td>
                    <td className="px-3 py-2 align-top font-mono text-xs whitespace-nowrap text-violet-300">{row.action}</td>
                    <td className="px-3 py-2 align-top text-xs whitespace-nowrap">{row.actor_username ?? "—"}</td>
                    <td className="px-3 py-2 align-top font-mono text-xs whitespace-nowrap">
                      {row.resource_type}:{row.resource_id}
                    </td>
                    <td className="max-w-xs px-3 py-2 align-top font-mono text-[11px] break-all text-slate-500">{jsonSnippet(row.before_json)}</td>
                    <td className="max-w-xs px-3 py-2 align-top font-mono text-[11px] break-all text-slate-400">{jsonSnippet(row.after_json)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {(logs.data.results?.length ?? 0) === 0 ? <p className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-8 text-center text-sm text-slate-500">No log rows match these filters.</p> : null}

          <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-slate-500">
            <span>
              Page {page} of {totalPages} · {logs.data.count} total
            </span>
            <div className="flex gap-2">
              <button
                className="rounded-md border border-slate-700 px-3 py-1.5 font-medium text-slate-300 hover:bg-slate-800 disabled:opacity-40"
                disabled={!logs.data.previous || logs.isFetching}
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <button
                className="rounded-md border border-slate-700 px-3 py-1.5 font-medium text-slate-300 hover:bg-slate-800 disabled:opacity-40"
                disabled={!logs.data.next || logs.isFetching}
                type="button"
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
