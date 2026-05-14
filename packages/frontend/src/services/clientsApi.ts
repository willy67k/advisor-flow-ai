import type { Client, ClientInput } from "../types/clients";

import { api } from "./api";

type Paginated<T> = {
  readonly results: readonly T[];
};

export async function fetchClients(): Promise {
  const { data } = await api.get<Paginated>("/api/clients/", {
    params: { page_size: 100 },
  });
  return [...data.results];
}

export async function createClient(body: ClientInput): Promise {
  const { data } = await api.post<Client>("/api/clients/", body);
  return data;
}

export async function updateClient(id: number, body: Partial): Promise {
  const { data } = await api.patch<Client>(`/api/clients/${id}/`, body);
  return data;
}

export async function deleteClient(id: number): Promise {
  await api.delete(`/api/clients/${id}/`);
}
