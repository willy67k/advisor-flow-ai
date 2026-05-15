import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createMeeting, deleteMeeting, fetchMeetings, updateMeeting } from "../services/meetingsApi";
import type { MeetingInput } from "../types/meetings";

export function useMeetings() {
  return useQuery({
    queryKey: ["meetings"],
    queryFn: fetchMeetings,
  });
}

export function useCreateMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: MeetingInput) => createMeeting(body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["meetings"] }),
  });
}

export function useUpdateMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<MeetingInput> }) => updateMeeting(id, body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["meetings"] }),
  });
}

export function useDeleteMeeting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteMeeting(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["meetings"] }),
  });
}
