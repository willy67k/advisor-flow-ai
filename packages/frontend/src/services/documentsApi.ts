import type { Document } from "../types/documents";

import { api } from "./api";

type Paginated<T> = {
  readonly results: readonly T[];
};

export async function uploadDocument(meetingId: number, file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("meeting", String(meetingId));
  formData.append("file", file);
  const { data } = await api.post<Document>("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function fetchDocument(id: number): Promise<Document> {
  const { data } = await api.get<Document>(`/api/documents/${id}`);
  return data;
}

export async function fetchDocumentsByMeeting(meetingId: number): Promise<Document[]> {
  const { data } = await api.get<Paginated<Document>>("/api/documents/", {
    params: { meeting: meetingId, page_size: 50 },
  });
  return [...data.results];
}
