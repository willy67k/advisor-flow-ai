export type WorkflowStatus = "pending" | "processing" | "waiting_compliance" | "waiting_approval" | "completed" | "failed" | "rejected";

export interface Workflow {
  readonly id: number;
  readonly status: WorkflowStatus;
  readonly meeting_id: number;
  readonly celery_task_id: string | null;
  readonly result_json: Record<string, unknown> | null;
  readonly pending_approval_id: number | null;
  readonly celery_state?: string;
}

/** Row from ``GET /api/workflows/`` (no heavy ``result_json``). */
export interface WorkflowListItem {
  readonly id: number;
  readonly status: WorkflowStatus;
  readonly meeting_id: number;
  readonly meeting_title: string;
  readonly pending_approval_id: number | null;
}
