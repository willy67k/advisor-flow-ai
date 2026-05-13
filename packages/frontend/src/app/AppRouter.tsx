import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../components/AppLayout.tsx";
import { GuestRoute } from "../components/GuestRoute.tsx";
import { ProtectedRoute } from "../components/ProtectedRoute.tsx";
import { LoginPage } from "../features/auth/LoginPage.tsx";
import { RegisterPage } from "../features/auth/RegisterPage.tsx";
import { ApprovalsPage } from "../pages/ApprovalsPage.tsx";
import { DashboardPage } from "../pages/DashboardPage.tsx";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<GuestRoute />}>
          <Route element={<LoginPage />} path="/login" />
          <Route element={<RegisterPage />} path="/register" />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route element={<Navigate replace to="/dashboard" />} index />
            <Route element={<DashboardPage />} path="dashboard" />
            <Route element={<ApprovalsPage />} path="approvals" />
          </Route>
        </Route>

        <Route element={<Navigate replace to="/dashboard" />} path="/" />
        <Route element={<Navigate replace to="/dashboard" />} path="*" />
      </Routes>
    </BrowserRouter>
  );
}
