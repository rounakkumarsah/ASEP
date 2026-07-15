import { useQuery } from "@tanstack/react-query";
import { projectsService } from "../services/projects";

export const projectKeys = {
  all: ["projects"] as const,
  lists: () => [...projectKeys.all, "list"] as const,
  list: (filters: string) => [...projectKeys.lists(), { filters }] as const,
  details: () => [...projectKeys.all, "detail"] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
};

export function useProjects() {
  return useQuery({
    queryKey: projectKeys.lists(),
    queryFn: async () => {
      // For now we use the scaffolded getStatus method as a placeholder
      // In reality, this would map to a getProjects API call.
      const response = await projectsService.getStatus();
      return response.data;
    },
  });
}
