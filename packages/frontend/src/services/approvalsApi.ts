import type { PendingApproval } from "../types/approvals.ts";

import { api } from "./api.ts";

export async function fetchPendingApprovals(): Promise {
  const { data } = await api.get("/api/approvals/pending");
  return data as PendingApproval[];
}

export async function approveApproval(id: number, note: string) {
  return api.post<{ workflow_id: number; result_json: Record }>(`/api/approvals/${id}/approve`, { note });
}

export async function rejectApproval(id: number, note: string) {
  return api.post<{ workflow_id: number; result_json: Record }>(`/api/approvals/${id}/reject`, { note });
}

export async function startMeetingSummaryWorkflow(meetingId: number) {
  return api.post<{ workflow_id: number }>("/api/workflows/start", {
    meeting_id: meetingId,
  });
}
