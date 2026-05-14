import type { Meeting, MeetingAiSummary, MeetingInput } from "../types/meetings";

import { api } from "./api";

type Paginated<T> = {
  readonly results: readonly T[];
};

export type { Meeting as MeetingRow };

export async function fetchMeeting(id: number): Promise {
  const { data } = await api.get<Meeting>(`/api/meetings/${id}/`);
  return data;
}

export async function fetchMeetingAiSummary(meetingId: number): Promise {
  const { data } = await api.get<MeetingAiSummary>(`/api/meetings/${meetingId}/ai-summary/`);
  return data;
}

export async function fetchMeetings(): Promise {
  const { data } = await api.get<Paginated>("/api/meetings/", {
    params: { page_size: 100 },
  });
  return [...data.results];
}

export async function createMeeting(body: MeetingInput): Promise {
  const { data } = await api.post<Meeting>("/api/meetings/", body);
  return data;
}

export async function updateMeeting(id: number, body: Partial): Promise {
  const { data } = await api.patch<Meeting>(`/api/meetings/${id}/`, body);
  return data;
}

export async function deleteMeeting(id: number): Promise {
  await api.delete(`/api/meetings/${id}/`);
}
