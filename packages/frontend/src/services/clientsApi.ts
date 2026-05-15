import type { Client, ClientInput } from "../types/clients";

import { api } from "./api";

type Paginated<T> = {
  readonly results: readonly T[];
};

export async function fetchClients(): Promise<Client[]> {
  const { data } = await api.get<Paginated<Client>>("/api/clients/", {
    params: { page_size: 100 },
  });
  return [...data.results];
}

export async function createClient(body: ClientInput): Promise<Client> {
  const { data } = await api.post<Client>("/api/clients/", body);
  return data;
}

export async function updateClient(id: number, body: Partial<ClientInput>): Promise<Client> {
  const { data } = await api.patch<Client>(`/api/clients/${id}/`, body);
  return data;
}

export async function deleteClient(id: number): Promise<void> {
  await api.delete(`/api/clients/${id}/`);
}
