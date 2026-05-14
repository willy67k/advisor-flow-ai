import { useState } from "react";

import { ClientModal } from "../features/clients/ClientModal";
import { useClients, useDeleteClient } from "../hooks/useClients";
import type { Client } from "../types/clients";

export function ClientsPage() {
  const { data: clients, status, isFetching, refetch } = useClients();
  const deleteMut = useDeleteClient();

  const [showModal, setShowModal] = useState(false);
  const [editTarget, setEditTarget] = useState<Client | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Client | null>(null);

  function openCreate() {
    setEditTarget(null);
    setShowModal(true);
  }

  function openEdit(client: Client) {
    setEditTarget(client);
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditTarget(null);
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    await deleteMut.mutateAsync(pendingDelete.id);
    setPendingDelete(null);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Clients</h1>
          <p className="mt-1 text-sm text-slate-400">Manage your client records.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="text-xs font-medium text-emerald-400 hover:text-emerald-300 disabled:opacity-50" disabled={isFetching} type="button" onClick={() => void refetch()}>
            {isFetching ? "Refreshing…" : "Refresh"}
          </button>
          <button className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400" type="button" onClick={openCreate}>
            + Add client
          </button>
        </div>
      </div>

      {status === "pending" ? (
        <p className="text-sm text-slate-500">Loading clients…</p>
      ) : status === "error" ? (
        <p className="text-sm text-rose-400">Unable to load clients. Check your connection and try again.</p>
      ) : (clients?.length ?? 0) === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/30 px-4 py-12 text-center">
          <p className="text-sm text-slate-500">No clients yet. Add your first client to get started.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80">
                <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Email</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Phone</th>
                <th className="px-4 py-3 text-right text-[11px] font-semibold tracking-wide text-slate-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(clients ?? []).map((client, idx) => (
                <tr key={client.id} className={`border-b border-slate-800/60 last:border-0 ${idx % 2 === 0 ? "bg-slate-900/30" : "bg-slate-900/10"}`}>
                  <td className="px-4 py-3 font-medium text-slate-100">{client.name}</td>
                  <td className="px-4 py-3 text-slate-400">{client.email || "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{client.phone || "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <button className="text-xs font-medium text-emerald-400 hover:text-emerald-300" type="button" onClick={() => openEdit(client)}>
                        Edit
                      </button>
                      <button className="text-xs font-medium text-rose-400 hover:text-rose-300" type="button" onClick={() => setPendingDelete(client)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal ? <ClientModal editTarget={editTarget} onClose={closeModal} /> : null}

      {pendingDelete ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setPendingDelete(null);
          }}
        >
          <div className="w-full max-w-sm rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h2 className="text-base font-semibold text-slate-100">Delete client?</h2>
            <p className="mt-2 text-sm text-slate-400">
              This will permanently remove <span className="font-medium text-slate-200">{pendingDelete.name}</span> and all associated data. This action cannot be undone.
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
