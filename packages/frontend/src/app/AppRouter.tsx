import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../components/AppLayout.tsx";
import { ComplianceOfficerRoute } from "../components/ComplianceOfficerRoute.tsx";
import { GuestRoute } from "../components/GuestRoute.tsx";
import { ManagerRoute } from "../components/ManagerRoute.tsx";
import { ProtectedRoute } from "../components/ProtectedRoute.tsx";
import { AIChatPage } from "../features/ai-chat/AIChatPage.tsx";
import { LoginPage } from "../features/auth/LoginPage.tsx";
import { RegisterPage } from "../features/auth/RegisterPage.tsx";
import { ClientsPage } from "../pages/ClientsPage.tsx";
import { AuditLogsPage } from "../pages/AuditLogsPage.tsx";
import { ObservabilityLogsPage } from "../pages/ObservabilityLogsPage.tsx";
import { ComplianceReviewsPage } from "../pages/ComplianceReviewsPage.tsx";
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
            <Route element={<ComplianceOfficerRoute />}>
              <Route element={<ComplianceReviewsPage />} path="compliance" />
            </Route>
            <Route element={<ManagerRoute />}>
              <Route element={<AuditLogsPage />} path="audit-logs" />
              <Route element={<ObservabilityLogsPage />} path="observability-logs" />
            </Route>
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
