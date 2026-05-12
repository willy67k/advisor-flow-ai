import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "../stores/authStore";

export function GuestRoute() {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (accessToken) {
    return <Navigate replace to="/dashboard" />;
  }
  return <Outlet />;
}
