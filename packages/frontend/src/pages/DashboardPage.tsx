import { useQuery } from "@tanstack/react-query";

import { fetchMe } from "../services/api";
import { useAuthStore } from "../stores/authStore";
import { roleLabel } from "../lib/roleLabel";

export function DashboardPage() {
  const storedUser = useAuthStore((s) => s.user);

  const {
    data: me,
    status,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
  });

  const display = me ?? storedUser;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Overview</h1>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">You’re signed in. Your profile and permissions are shown below. When more tools are available, they’ll appear in the sidebar.</p>
      </div>

      <div className="max-w-xl rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-sm font-semibold text-slate-200">Your profile</h2>
          <button type="button" className="text-xs font-medium text-emerald-400 hover:text-emerald-300 disabled:opacity-50" disabled={isFetching} onClick={() => void refetch()}>
            {isFetching ? "Updating…" : "Refresh"}
          </button>
        </div>
        {status === "pending" ? <p className="mt-4 text-sm text-slate-500">Loading profile…</p> : null}
        {status === "error" ? <p className="mt-4 text-sm text-rose-400">We couldn’t load your profile. Check your connection, then tap Refresh.</p> : null}
        {display ? (
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-[11px] tracking-wide text-slate-500 uppercase">Username</dt>
              <dd className="font-medium text-slate-100">{display.username}</dd>
            </div>
            <div>
              <dt className="text-[11px] tracking-wide text-slate-500 uppercase">Role</dt>
              <dd className="font-medium text-emerald-400">{roleLabel(display.role)}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-[11px] tracking-wide text-slate-500 uppercase">Email</dt>
              <dd className="text-slate-300">{display.email || "—"}</dd>
            </div>
          </dl>
        ) : null}
      </div>
    </div>
  );
}
