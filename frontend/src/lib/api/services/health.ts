import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const healthService = {
  // Scaffolded service for health
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/health/status');
    return response.data;
  }
};
