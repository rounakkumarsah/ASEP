import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const evaluationService = {
  // Scaffolded service for evaluation
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/evaluation/status');
    return response.data;
  }
};
