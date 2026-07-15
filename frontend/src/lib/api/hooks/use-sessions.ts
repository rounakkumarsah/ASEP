import { useQuery } from "@tanstack/react-query";
import { sessionsService } from "../services/sessions";

export const sessionKeys = {
  all: ["sessions"] as const,
  lists: () => [...sessionKeys.all, "list"] as const,
  list: (filters: string) => [...sessionKeys.lists(), { filters }] as const,
  details: () => [...sessionKeys.all, "detail"] as const,
  detail: (id: string) => [...sessionKeys.details(), id] as const,
};

export function useSessions() {
  return useQuery({
    queryKey: sessionKeys.lists(),
    queryFn: async () => {
      const response = await sessionsService.getSessions();
      return response.data;
    },
    // Poll every 5 seconds for live agent session updates
    refetchInterval: 5000,
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: sessionKeys.detail(id),
    queryFn: async () => {
      const response = await sessionsService.getSession(id);
      return response.data;
    },
    // Poll every 3 seconds for active detail view
    refetchInterval: 3000,
    enabled: !!id,
  });
}
