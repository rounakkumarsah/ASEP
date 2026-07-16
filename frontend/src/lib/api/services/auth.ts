import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const authService = {
  // Scaffolded service for auth
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get("/api/v1/auth/status");
    return response.data;
  },
};
