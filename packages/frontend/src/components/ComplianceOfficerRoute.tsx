import { useQuery } from "@tanstack/react-query";
import { Navigate, Outlet } from "react-router-dom";

import { fetchMe } from "../services/api";
import { useAuthStore } from "../stores/authStore";

const ROLE = "compliance_officer";

/** Only ``compliance_officer`` users may access nested routes; loads profile if needed. */
export function ComplianceOfficerRoute() {
  const stored = useAuthStore((s) => s.user);
  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
    staleTime: 60_000,
  });

  if (meQuery.isPending && !stored) {
    return <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-6 py-10 text-center text-sm text-slate-400">Checking your access…</div>;
  }

  if (meQuery.isError && !stored) {
    return <Navigate replace to="/dashboard" />;
  }

  const role = meQuery.data?.role ?? stored?.role;
  if (role !== ROLE) {
    return <Navigate replace to="/dashboard" />;
  }

  return <Outlet />;
}
