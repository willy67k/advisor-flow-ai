import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { fetchObservabilityLogs } from "../services/observabilityLogsApi";

const CATEGORIES = ["", "ai_completion", "http_exception", "celery_failure"] as const;
const SEVERITIES = ["", "info", "warning", "error"] as const;

function jsonSnippet(value: Record<string, unknown>): string {
  try {
    const s = JSON.stringify(value, null, 0);
    return s.length > 220 ? `${s.slice(0, 217)}…` : s;
  } catch {
    return "—";
  }
}

export function ObservabilityLogsPage() {
  const [page, setPage] = useState(1);
  const [draftCategory, setDraftCategory] = useState<string>("");
  const [draftSeverity, setDraftSeverity] = useState<string>("");
  const [applied, setApplied] = useState<{ readonly category?: string; readonly severity?: string } | null>(null);
  const [searchEpoch, setSearchEpoch] = useState(0);

  const logs = useQuery({
    queryKey: ["observability-logs", searchEpoch, page, applied?.category ?? "", applied?.severity ?? ""],
    queryFn: () =>
      fetchObservabilityLogs(page, {
        category: applied?.category,
        severity: applied?.severity,
      }),
    enabled: applied !== null,
  });

  function handleSearch() {
    setPage(1);
    const c = draftCategory.trim();
    const s = draftSeverity.trim();
    setApplied({
      category: c || undefined,
      severity: s || undefined,
    });
    setSearchEpoch((n) => n + 1);
  }

  const pageSize = 25;
  const totalPages = logs.data ? Math.max(1, Math.ceil(logs.data.count / pageSize)) : 1;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Observability logs</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
          Structured events persisted from Phase 8.2 (AI completions, HTTP exceptions, Celery failures). Managers only. Click Search to load; filters use exact category / severity values.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Category
          <select className="w-52 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100" value={draftCategory} onChange={(e) => setDraftCategory(e.target.value)}>
            <option value="">All</option>
            {CATEGORIES.filter(Boolean).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Severity
          <select className="w-40 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-100" value={draftSeverity} onChange={(e) => setDraftSeverity(e.target.value)}>
            <option value="">All</option>
            {SEVERITIES.filter(Boolean).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <button className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50" disabled={logs.isFetching} type="button" onClick={() => handleSearch()}>
          Search
        </button>
      </div>

      {applied === null ? <p className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-10 text-center text-sm text-slate-500">Choose filters if needed, then click Search to load observability logs.</p> : null}

      {applied !== null && logs.status === "pending" ? <p className="text-sm text-slate-500">Loading…</p> : null}
      {applied !== null && logs.status === "error" ? <p className="text-sm text-rose-400">Unable to load observability logs.</p> : null}

      {applied !== null && logs.status === "success" ? (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
              <thead className="bg-slate-900/80 text-xs tracking-wide text-slate-400 uppercase">
                <tr>
                  <th className="px-3 py-2 font-medium whitespace-nowrap">Time</th>
                  <th className="px-3 py-2 font-medium whitespace-nowrap">Category</th>
                  <th className="px-3 py-2 font-medium whitespace-nowrap">Severity</th>
                  <th className="min-w-[18rem] px-3 py-2 font-medium">Payload</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-200">
                {(logs.data.results ?? []).map((row) => (
                  <tr key={row.id} className="bg-slate-950/40 hover:bg-slate-900/60">
                    <td className="px-3 py-2 align-top text-xs whitespace-nowrap text-slate-400">{new Date(row.created_at).toLocaleString()}</td>
                    <td className="px-3 py-2 align-top font-mono text-xs whitespace-nowrap text-cyan-300">{row.category}</td>
                    <td className="px-3 py-2 align-top font-mono text-xs whitespace-nowrap text-amber-300">{row.severity}</td>
                    <td className="max-w-xl px-3 py-2 align-top font-mono text-[11px] break-all text-slate-400">{jsonSnippet(row.payload)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {(logs.data.results?.length ?? 0) === 0 ? <p className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-8 text-center text-sm text-slate-500">No rows match these filters.</p> : null}

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
