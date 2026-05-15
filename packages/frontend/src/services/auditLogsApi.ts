import { api } from "./api";
import type { AuditLogPage } from "../types/auditLog";

export async function fetchAuditLogs(page = 1, opts?: { readonly resourceType?: string; readonly resourceId?: string }): Promise<AuditLogPage> {
  const { data } = await api.get<AuditLogPage>("/api/audit-logs/", {
    params: {
      page,
      ...(opts?.resourceType?.trim() ? { resource_type: opts.resourceType.trim() } : {}),
      ...(opts?.resourceId?.trim() ? { resource_id: opts.resourceId.trim() } : {}),
    },
  });
  return data;
}
