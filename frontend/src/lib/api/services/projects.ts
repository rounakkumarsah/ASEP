import { apiClient } from "../client";
import { ApiResponse } from "../types";

export interface ProjectData {
  id: string;
  org_id: string;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
}

export const projectsService = {
  async getProjects(): Promise<ApiResponse<ProjectData[]>> {
    const response = await apiClient.get("/api/v1/projects");
    return {
      status: "success",
      data: response.data,
    };
  },
};
