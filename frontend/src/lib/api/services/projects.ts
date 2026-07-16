import { apiClient } from "../client";
import { ApiResponse } from "../types";

export const projectsService = {
  // Scaffolded service for projects
  async getStatus(): Promise<ApiResponse<unknown>> {
    const response = await apiClient.get("/api/v1/projects/status");
    return response.data;
  },
};
