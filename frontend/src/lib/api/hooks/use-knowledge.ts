import { useQuery } from "@tanstack/react-query";
import { knowledgeService } from "../services/knowledge";

export const knowledgeKeys = {
  all: ["knowledge"] as const,
  lists: () => [...knowledgeKeys.all, "list"] as const,
  list: (query?: string) => [...knowledgeKeys.lists(), { query }] as const,
};

export function useKnowledge(query?: string) {
  return useQuery({
    queryKey: knowledgeKeys.list(query),
    queryFn: async () => {
      const response = await knowledgeService.getDocuments(query);
      return response.data;
    },
  });
}
