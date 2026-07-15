import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const knowledgeService = {
  // Scaffolded service for knowledge
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/knowledge/status');
    return response.data;
  }
};
