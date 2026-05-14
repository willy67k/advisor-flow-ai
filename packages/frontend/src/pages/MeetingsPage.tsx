import { useState } from "react";
import { Link } from "react-router-dom";

import { DocumentUpload } from "../features/meetings/DocumentUpload";
import { MeetingModal } from "../features/meetings/MeetingModal";
import { useClients } from "../hooks/useClients";
import { useDeleteMeeting, useMeetings } from "../hooks/useMeetings";
import type { Meeting } from "../types/meetings";

export function MeetingsPage() {
  const { data: meetings, status, isFetching, refetch } = useMeetings();
  const { data: clients } = useClients();
  const deleteMut = useDeleteMeeting();

  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState<Meeting | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Meeting | null>(null);

  const clientMap = new Map((clients ?? []).map((c) => [c.id, c.name]));

  function openCreate() {
    setEditTarget(null);
    setShowModal(true);
  }

  function openEdit(meeting: Meeting) {
    setEditTarget(meeting);
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditTarget(null);
  }

  function toggleExpand(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    await deleteMut.mutateAsync(pendingDelete.id);
    setPendingDelete(null);
    if (expandedId === pendingDelete.id) setExpandedId(null);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Meetings</h1>
          <p className="mt-1 text-sm text-slate-400">Track meeting records and associated documents.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="text-xs font-medium text-emerald-400 hover:text-emerald-300 disabled:opacity-50" disabled={isFetching} type="button" onClick={() => void refetch()}>
            {isFetching ? "Refreshing…" : "Refresh"}
          </button>
          <button className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400" type="button" onClick={openCreate}>
            + New meeting
          </button>
        </div>
      </div>

      {status === "pending" ? (
        <p className="text-sm text-slate-500">Loading meetings…</p>
      ) : status === "error" ? (
        <p className="text-sm text-rose-400">Unable to load meetings. Check your connection and try again.</p>
      ) : (meetings?.length ?? 0) === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-12 text-center">
          <p className="text-sm text-slate-500">No meetings yet. Create your first meeting to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {(meetings ?? []).map((meeting) => (
            <div key={meeting.id} className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="flex items-center gap-3 px-5 py-4">
                <button className="mr-1 text-slate-500 hover:text-slate-300" type="button" onClick={() => toggleExpand(meeting.id)} aria-label={expandedId === meeting.id ? "Collapse" : "Expand"}>
                  <svg className={`h-4 w-4 transition-transform ${expandedId === meeting.id ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <div className="min-w-0 flex-1">
                  <button className="text-left" type="button" onClick={() => toggleExpand(meeting.id)}>
                    <p className="font-medium text-slate-100 hover:text-white">{meeting.title}</p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {meeting.date}
                      {clientMap.has(meeting.client) ? ` · ${clientMap.get(meeting.client)}` : null}
                    </p>
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  <Link className="text-xs font-medium text-slate-300 hover:text-white" to={`/meetings/${meeting.id}`}>
                    Detail
                  </Link>
                  <button className="text-xs font-medium text-emerald-400 hover:text-emerald-300" type="button" onClick={() => openEdit(meeting)}>
                    Edit
                  </button>
                  <button className="text-xs font-medium text-rose-400 hover:text-rose-300" type="button" onClick={() => setPendingDelete(meeting)}>
                    Delete
                  </button>
                </div>
              </div>

              {expandedId === meeting.id ? (
                <div className="space-y-4 border-t border-slate-800 px-5 py-4">
                  {meeting.notes ? (
                    <div>
                      <p className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Notes</p>
                      <p className="mt-2 text-sm leading-relaxed whitespace-pre-wrap text-slate-300">{meeting.notes}</p>
                    </div>
                  ) : null}

                  <div>
                    <p className="mb-3 text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Documents</p>
                    <DocumentUpload meetingId={meeting.id} />
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}

      {showModal ? <MeetingModal editTarget={editTarget} onClose={closeModal} /> : null}

      {pendingDelete ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setPendingDelete(null);
          }}
        >
          <div className="w-full max-w-sm rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-base font-semibold text-slate-100">Delete meeting?</h2>
            <p className="mt-2 text-sm text-slate-400">
              This will permanently remove <span className="font-medium text-slate-200">{pendingDelete.title}</span> and all associated documents and workflows.
            </p>
            <div className="mt-5 flex justify-end gap-3">
              <button className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:border-slate-500 hover:bg-slate-800" disabled={deleteMut.isPending} type="button" onClick={() => setPendingDelete(null)}>
                Cancel
              </button>
              <button className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-500 disabled:opacity-50" disabled={deleteMut.isPending} type="button" onClick={() => void confirmDelete()}>
                {deleteMut.isPending ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
