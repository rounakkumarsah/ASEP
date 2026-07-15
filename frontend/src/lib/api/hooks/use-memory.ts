import { useQuery } from "@tanstack/react-query";
import { memoryService } from "../services/memory";
import { MemoryType } from "../types";

export const memoryKeys = {
  all: ["memories"] as const,
  lists: () => [...memoryKeys.all, "list"] as const,
  list: (type?: MemoryType, query?: string) => [...memoryKeys.lists(), { type, query }] as const,
};

export function useMemories(type?: MemoryType, query?: string) {
  return useQuery({
    queryKey: memoryKeys.list(type, query),
    queryFn: async () => {
      const response = await memoryService.getMemories(type, query);
      return response.data;
    },
  });
}
