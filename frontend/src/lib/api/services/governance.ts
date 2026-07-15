import { ApiResponse, PaginatedResponse, ApprovalRequest, GovernancePolicy, AuditRecord } from "../types";

const mockApprovals: ApprovalRequest[] = [
  {
    id: "app_01",
    resourceId: "db_prod_users",
    agentId: "agent_migration_01",
    requestedAction: "DROP TABLE users_backup",
    status: "pending",
    riskLevel: "critical",
    justification: "Cleanup of old backup tables to free up storage space.",
    requestedAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
  },
  {
    id: "app_02",
    resourceId: "api_stripe_key",
    agentId: "agent_billing_99",
    requestedAction: "READ secret api_stripe_key",
    status: "approved",
    riskLevel: "high",
    justification: "Process monthly subscription renewals.",
    requestedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
    resolvedAt: new Date(Date.now() - 1000 * 60 * 50).toISOString(),
    resolvedBy: "admin@asep.dev",
  },
  {
    id: "app_03",
    resourceId: "aws_ec2_instances",
    agentId: "agent_infra_05",
    requestedAction: "TERMINATE instance i-0abcd1234efgh5678",
    status: "denied",
    riskLevel: "medium",
    justification: "Scale down underutilized resources.",
    requestedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
    resolvedAt: new Date(Date.now() - 1000 * 60 * 60 * 23).toISOString(),
    resolvedBy: "secops@asep.dev",
  }
];

const mockPolicies: GovernancePolicy[] = [
  {
    id: "pol_01",
    name: "Production Database Write Protection",
    description: "All write/delete operations to production databases require explicit human approval.",
    isActive: true,
    riskThreshold: "high",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
  },
  {
    id: "pol_02",
    name: "Secrets Access Policy",
    description: "Agents may access staging secrets autonomously but production secrets require approval.",
    isActive: true,
    riskThreshold: "critical",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(),
  }
];

const mockAudits: AuditRecord[] = [
  {
    id: "aud_01",
    action: "READ_SECRET",
    actor: "agent_billing_99",
    target: "api_stripe_key",
    status: "success",
    timestamp: new Date(Date.now() - 1000 * 60 * 50).toISOString(),
    metadata: { approvalId: "app_02" }
  },
  {
    id: "aud_02",
    action: "TERMINATE_INSTANCE",
    actor: "agent_infra_05",
    target: "i-0abcd1234efgh5678",
    status: "blocked",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 23).toISOString(),
    metadata: { reason: "Policy Denied" }
  }
];

export const governanceService = {
  async getApprovals(): Promise<ApiResponse<PaginatedResponse<ApprovalRequest>>> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: "success",
          data: { items: mockApprovals, total: mockApprovals.length, page: 1, size: 50, pages: 1 }
        });
      }, 400);
    });
  },
  
  async getPolicies(): Promise<ApiResponse<PaginatedResponse<GovernancePolicy>>> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: "success",
          data: { items: mockPolicies, total: mockPolicies.length, page: 1, size: 50, pages: 1 }
        });
      }, 400);
    });
  },

  async getAudits(): Promise<ApiResponse<PaginatedResponse<AuditRecord>>> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: "success",
          data: { items: mockAudits, total: mockAudits.length, page: 1, size: 50, pages: 1 }
        });
      }, 400);
    });
  }
};
