export type AuditLogRow = {
  id: number;
  actor: number | null;
  actor_username: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  token_usage: Record<string, unknown> | null;
  created_at: string;
};

export type AuditLogPage = {
  count: number;
  next: string | null;
  previous: string | null;
  results: AuditLogRow[];
};
