import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const controlPlaneService = {
  // Scaffolded service for control-plane
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get('/api/v1/control-plane/status');
    return response.data;
  }
};
