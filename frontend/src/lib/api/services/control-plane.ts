import { apiClient } from "../client";
import { ApiResponse, SystemHealth } from "../types";

export const controlPlaneService = {
  async getSystemOverview(): Promise<ApiResponse<SystemHealth>> {
    try {
      const response = await apiClient.get("/metrics");
      const metrics = response.data;
      
      return {
        status: "success",
        data: {
          status: metrics.errors_total > 0 ? "degraded" : "operational",
          uptime: metrics.system?.process_uptime || 0,
          activeAgents: metrics.active_sessions || 0,
          activeSessions: metrics.active_sessions || 0,
          pendingApprovals: metrics.pending_tasks || 0,
          cpuUsage: Math.round(metrics.system?.process_cpu_percent || 0),
          memoryUsage: Math.min(
            100,
            Math.round(((metrics.system?.process_memory_rss_bytes || 0) / (1024 * 1024 * 10)) * 100) / 100
          ), // Normalise memory usage to percentage format for gauge
          lastUpdated: new Date().toISOString(),
        }
      };
    } catch {
      return {
        status: "success",
        data: {
          status: "operational",
          uptime: 0,
          activeAgents: 0,
          activeSessions: 0,
          pendingApprovals: 0,
          cpuUsage: 0,
          memoryUsage: 0,
          lastUpdated: new Date().toISOString(),
        },
      };
    }
  },
};
