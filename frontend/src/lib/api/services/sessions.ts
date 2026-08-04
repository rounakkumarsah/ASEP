import { ApiResponse, Session } from "../types";

import { apiClient } from "../client";

export const sessionsService = {
  async getSessions(): Promise<ApiResponse<Session[]>> {
    try {
      const response = await apiClient.get('/api/v1/sessions');
      return {
        status: "success",
        data: response.data.items || response.data || [],
      };
    } catch {
      // If the backend endpoint is missing, return empty instead of failing hard
      return {
        status: "success",
        data: [],
      };
    }
  },

  async getSession(id: string): Promise<ApiResponse<Session>> {
    const response = await apiClient.get(`/api/v1/sessions/${id}`);
    return {
      status: "success",
      data: response.data,
    };
  },
};
