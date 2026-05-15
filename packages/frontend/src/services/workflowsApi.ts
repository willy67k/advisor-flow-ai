import type { Workflow, WorkflowListItem } from "../types/workflows";

import { api } from "./api";

type Paginated<T> = {
  readonly results: readonly T[];
};

export async function fetchWorkflow(id: number): Promise<Workflow> {
  const { data } = await api.get<Workflow>(`/api/workflows/${id}`);
  return data;
}

export async function fetchWorkflowList(pageSize = 40): Promise<WorkflowListItem[]> {
  const { data } = await api.get<Paginated<WorkflowListItem>>("/api/workflows/", {
    params: { page_size: pageSize },
  });
  return [...data.results];
}
