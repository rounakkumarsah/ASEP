import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const auditService = {
  // Scaffolded service for audit
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/audit/status');
    return response.data;
  }
};
