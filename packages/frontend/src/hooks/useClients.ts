import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createClient, deleteClient, fetchClients, updateClient } from "../services/clientsApi";
import type { ClientInput } from "../types/clients";

export function useClients() {
  return useQuery({
    queryKey: ["clients"],
    queryFn: fetchClients,
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ClientInput) => createClient(body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}

export function useUpdateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial }) => updateClient(id, body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}

export function useDeleteClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteClient(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}
