export type AiDraftActionItem = {
  readonly task: string;
  readonly owner?: string | null;
  readonly due?: string | null;
};

export type AiDraftJson = {
  readonly summary: string;
  readonly action_items?: readonly AiDraftActionItem[];
};

export type PendingApproval = {
  readonly id: number;
  readonly workflow_id: number;
  readonly meeting_id: number;
  readonly meeting_title: string;
  readonly ai_draft_json: AiDraftJson;
};
