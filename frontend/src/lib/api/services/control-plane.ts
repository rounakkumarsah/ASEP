import { ApiResponse, SystemHealth } from "../types";

export const controlPlaneService = {
  async getSystemOverview(): Promise<ApiResponse<SystemHealth>> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: "success",
          data: {
            status: "operational",
            uptime: 1209600, // 14 days
            activeAgents: 12,
            activeSessions: 3,
            pendingApprovals: 5,
            cpuUsage: 45,
            memoryUsage: 68,
            lastUpdated: new Date().toISOString()
          }
        });
      }, 400); // Simulate network latency
    });
  }
};
