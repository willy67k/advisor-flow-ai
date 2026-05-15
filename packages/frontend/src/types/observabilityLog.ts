export type ObservabilityLogRow = {
  id: number;
  category: string;
  severity: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type ObservabilityLogPage = {
  count: number;
  next: string | null;
  previous: string | null;
  results: ObservabilityLogRow[];
};
