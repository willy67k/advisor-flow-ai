import { NavLink, Outlet, useLocation } from "react-router-dom";

import { roleLabel } from "../lib/roleLabel";
import { logoutRequest } from "../services/api";
import { useAuthStore } from "../stores/authStore";

const navClass = ({ isActive }: { readonly isActive: boolean }) =>
  ["block cursor-pointer rounded-md px-3 py-2 text-sm font-medium transition-colors", isActive ? "bg-slate-700 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"].join(" ");

const NAV_ITEMS = [
  { to: "/dashboard", label: "Overview" },
  { to: "/clients", label: "Clients" },
  { to: "/meetings", label: "Meetings" },
  { to: "/documents", label: "Documents" },
  { to: "/meeting-summary", label: "Meeting summary" },
  { to: "/chat", label: "AI Chat" },
] as const;

const ROUTE_TITLE: Record = {
  dashboard: "Overview",
  clients: "Clients",
  meetings: "Meetings",
  documents: "Documents",
  "meeting-summary": "Meeting summary",
  chat: "AI Chat",
};

function layoutTitle(pathname: string): string {
  const segments = pathname.split("/").filter(Boolean);
  const first = segments[0] ?? "";
  const second = segments[1] ?? "";

  if (first === "meetings" && second !== "" && /^\d+$/.test(second)) {
    return "Meeting detail";
  }
  if (first && ROUTE_TITLE[first]) {
    return ROUTE_TITLE[first];
  }
  return "AdvisorFlow";
}

export function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  const headerTitle = layoutTitle(location.pathname);

  async function handleLogout() {
    await logoutRequest().catch(() => undefined);
    window.location.assign("/login");
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <aside className="flex w-56 shrink-0 flex-col border-r border-slate-800 bg-slate-900/90">
        <div className="border-b border-slate-800 px-4 py-4">
          <p className="text-xs tracking-[0.2em] text-slate-500 uppercase">AdvisorFlow</p>
          <p className="font-semibold text-slate-100">Workspace</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {NAV_ITEMS.map(({ to, label }) => (
            <NavLink key={to} className={(p) => navClass(p)} end={to !== "/meetings"} to={to}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-slate-800 px-6">
          <span className="text-sm font-medium text-slate-300">{headerTitle}</span>
          <div className="flex items-center gap-4">
            {user ? (
              <span className="hidden text-xs text-slate-500 md:inline">
                {user.username} · <span className="text-emerald-400">{roleLabel(user.role)}</span>
              </span>
            ) : null}
            <button className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:border-slate-500" type="button" onClick={() => void handleLogout()}>
              Log out
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
