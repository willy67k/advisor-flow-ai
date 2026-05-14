import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../components/AppLayout.tsx";
import { GuestRoute } from "../components/GuestRoute.tsx";
import { ProtectedRoute } from "../components/ProtectedRoute.tsx";
import { AIChatPage } from "../features/ai-chat/AIChatPage.tsx";
import { LoginPage } from "../features/auth/LoginPage.tsx";
import { RegisterPage } from "../features/auth/RegisterPage.tsx";
import { ClientsPage } from "../pages/ClientsPage.tsx";
import { DashboardPage } from "../pages/DashboardPage.tsx";
import { DocumentsPage } from "../pages/DocumentsPage.tsx";
import { MeetingDetailPage } from "../pages/MeetingDetailPage.tsx";
import { MeetingSummaryPage } from "../pages/MeetingSummaryPage.tsx";
import { MeetingsPage } from "../pages/MeetingsPage.tsx";

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
            <Route element={<ClientsPage />} path="clients" />
            <Route element={<MeetingDetailPage />} path="meetings/:meetingId" />
            <Route element={<MeetingsPage />} path="meetings" />
            <Route element={<DocumentsPage />} path="documents" />
            <Route element={<MeetingSummaryPage />} path="meeting-summary" />
            <Route element={<Navigate replace to="/meeting-summary" />} path="workflows" />
            <Route element={<Navigate replace to="/meeting-summary" />} path="approvals" />
            <Route element={<AIChatPage />} path="chat" />
          </Route>
        </Route>

        <Route element={<Navigate replace to="/dashboard" />} path="/" />
        <Route element={<Navigate replace to="/dashboard" />} path="*" />
      </Routes>
    </BrowserRouter>
  );
}
