import {
  ApiResponse,
  MemoryItem,
  MemoryType,
  PaginatedResponse,
} from "../types";

import { apiClient } from "../client";

export const memoryService = {
  async getMemories(
    type?: MemoryType,
    query?: string,
  ): Promise<ApiResponse<PaginatedResponse<MemoryItem>>> {
    try {
      const response = await apiClient.get('/api/v1/memory', { params: { type, query } });
      return {
        status: "success",
        data: response.data || { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    } catch {
      return {
        status: "success",
        data: { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    }
  },
};
