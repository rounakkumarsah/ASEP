import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const sessionsService = {
  // Scaffolded service for sessions
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/sessions/status');
    return response.data;
  }
};
