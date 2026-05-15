import { api } from "./api";
import type { ObservabilityLogPage } from "../types/observabilityLog";

export async function fetchObservabilityLogs(page = 1, opts?: { readonly category?: string; readonly severity?: string }): Promise<ObservabilityLogPage> {
  const { data } = await api.get<ObservabilityLogPage>("/api/observability-logs/", {
    params: {
      page,
      ...(opts?.category ? { category: opts.category } : {}),
      ...(opts?.severity ? { severity: opts.severity } : {}),
    },
  });
  return data;
}
