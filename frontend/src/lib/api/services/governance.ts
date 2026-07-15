import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const governanceService = {
  // Scaffolded service for governance
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/governance/status');
    return response.data;
  }
};
