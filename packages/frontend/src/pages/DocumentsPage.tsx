import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { fetchDocumentsByMeeting } from "../services/documentsApi";
import { fetchMeetings } from "../services/meetingsApi";
import type { DocumentStatus } from "../types/documents";

const STATUS_LABEL: Record = {
  uploaded: "Queued",
  processing: "Processing",
  ready: "Ready",
};

const STATUS_COLOR: Record = {
  uploaded: "bg-slate-700 text-slate-300",
  processing: "bg-amber-500/20 text-amber-400",
  ready: "bg-emerald-500/20 text-emerald-400",
};

export function DocumentsPage() {
  const [selectedMeetingId, setSelectedMeetingId] = useState<number | "">("");

  const meetings = useQuery({
    queryKey: ["meetings", "list"],
    queryFn: fetchMeetings,
  });

  const docs = useQuery({
    queryKey: ["documents", "by-meeting", selectedMeetingId],
    queryFn: () => (selectedMeetingId !== "" ? fetchDocumentsByMeeting(selectedMeetingId) : Promise.resolve([])),
    enabled: selectedMeetingId !== "",
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Documents</h1>
        <p className="mt-1 text-sm text-slate-400">View uploaded documents and their processing status.</p>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-xs font-medium text-slate-400" htmlFor="doc-meeting-filter">
          Filter by meeting
        </label>
        <select
          id="doc-meeting-filter"
          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none disabled:opacity-50"
          disabled={meetings.status === "pending"}
          value={selectedMeetingId === "" ? "" : String(selectedMeetingId)}
          onChange={(e) => {
            const v = e.target.value;
            setSelectedMeetingId(v === "" ? "" : Number(v));
          }}
        >
          <option value="">{meetings.status === "pending" ? "Loading…" : "All meetings"}</option>
          {(meetings.data ?? []).map((m) => (
            <option key={m.id} value={m.id}>
              {m.title} (#{m.id})
            </option>
          ))}
        </select>
        {selectedMeetingId !== "" && docs.isFetching ? <span className="text-xs text-slate-500">Loading…</span> : null}
      </div>

      {selectedMeetingId === "" ? (
        <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-12 text-center">
          <p className="text-sm text-slate-500">Select a meeting to view its documents.</p>
        </div>
      ) : docs.status === "error" ? (
        <p className="text-sm text-rose-400">Unable to load documents.</p>
      ) : (docs.data?.length ?? 0) === 0 && docs.status === "success" ? (
        <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-12 text-center">
          <p className="text-sm text-slate-500">No documents for this meeting yet. Upload them from the Meetings page.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80">
                <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">File name</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">ID</th>
              </tr>
            </thead>
            <tbody>
              {(docs.data ?? []).map((doc, idx) => (
                <tr key={doc.id} className={`border-b border-slate-800/60 last:border-0 ${idx % 2 === 0 ? "bg-slate-900/30" : "bg-slate-900/10"}`}>
                  <td className="px-4 py-3 font-medium text-slate-100">{doc.file_name}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_COLOR[doc.status]}`}>{STATUS_LABEL[doc.status]}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">#{doc.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
