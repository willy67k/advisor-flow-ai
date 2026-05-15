import type { CompliancePendingItem, ComplianceWorkflowActionResponse } from "../types/compliance";

import { api } from "./api";

export async function fetchCompliancePending(): Promise<CompliancePendingItem[]> {
  const { data } = await api.get<CompliancePendingItem[]>("/api/compliance/pending");
  return [...data];
}

export async function clearComplianceHold(workflowId: number, note: string) {
  const { data } = await api.post<ComplianceWorkflowActionResponse>(`/api/compliance/workflows/${workflowId}/clear`, { note });
  return data;
}

export async function rejectComplianceHold(workflowId: number, note: string) {
  const { data } = await api.post<ComplianceWorkflowActionResponse>(`/api/compliance/workflows/${workflowId}/reject`, { note });
  return data;
}
