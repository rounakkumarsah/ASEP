import { ApiResponse, KnowledgeDocument, PaginatedResponse } from "../types";

import { apiClient } from "../client";

export const knowledgeService = {
  async getDocuments(
    query?: string,
  ): Promise<ApiResponse<PaginatedResponse<KnowledgeDocument>>> {
    try {
      const response = await apiClient.get('/api/v1/knowledge/documents', { params: { query } });
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
