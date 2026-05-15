export interface Meeting {
  readonly id: number;
  readonly title: string;
  readonly date: string;
  readonly notes: string;
  readonly client: number;
  readonly advisor: number;
}

export interface MeetingInput {
  title: string;
  date: string;
  notes: string;
  client: number;
}

export type MeetingAiSummaryActionItem = {
  readonly task: string;
  readonly owner?: string | null;
  readonly due?: string | null;
};

export interface MeetingAiSummary {
  readonly meeting_id: number;
  readonly workflow_id: number | null;
  readonly workflow_status: string | null;
  readonly pending_approval_id: number | null;
  readonly has_approved_summary: boolean;
  readonly summary: string | null;
  readonly action_items: readonly MeetingAiSummaryActionItem[];
  readonly approval_decision_note: string | null;
  /** Present when GET /ai-summary/ includes compliance outcome (backend Step 7.1+). */
  readonly compliance_rejected?: boolean;
  readonly compliance_decision_note?: string | null;
}
