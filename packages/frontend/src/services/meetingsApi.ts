import { api } from "./api.ts";

export type MeetingRow = {
  readonly id: number;
  readonly title: string;
  readonly notes: string;
  readonly client: number;
  readonly advisor: number;
};

type Paginated<T> = {
  readonly results: readonly T[];
};

export async function fetchMeetings(): Promise {
  const { data } = await api.get<Paginated>("/api/meetings/", {
    params: { page_size: 100 },
  });
  return [...data.results];
}
