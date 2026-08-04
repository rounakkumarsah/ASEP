import {
  ApiResponse,
  PaginatedResponse,
  ApprovalRequest,
  GovernancePolicy,
  AuditRecord,
} from "../types";

import { apiClient } from "../client";

export const governanceService = {
  async getApprovals(): Promise<
    ApiResponse<PaginatedResponse<ApprovalRequest>>
  > {
    try {
      const response = await apiClient.get('/api/v1/governance/hitl/queue');
      return {
        status: "success",
        data: response.data || { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    } catch {
      return {
        status: "success",
        data: { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    }
  },

  async getPolicies(): Promise<
    ApiResponse<PaginatedResponse<GovernancePolicy>>
  > {
    try {
      const response = await apiClient.get('/api/v1/governance/policies');
      return {
        status: "success",
        data: response.data || { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    } catch {
      return {
        status: "success",
        data: { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    }
  },

  async getAudits(): Promise<ApiResponse<PaginatedResponse<AuditRecord>>> {
    try {
      const response = await apiClient.get('/api/v1/audit/logs');
      return {
        status: "success",
        data: response.data || { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    } catch {
      return {
        status: "success",
        data: { items: [], total: 0, page: 1, size: 50, pages: 1 }
      };
    }
  },
};
