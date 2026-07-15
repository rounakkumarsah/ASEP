import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const memoryService = {
  // Scaffolded service for memory
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/memory/status');
    return response.data;
  }
};
