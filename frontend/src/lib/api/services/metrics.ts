import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const metricsService = {
  // Scaffolded service for metrics
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get("/api/v1/metrics/status");
    return response.data;
  },
};
