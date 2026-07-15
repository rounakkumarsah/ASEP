export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Session Models
export enum SessionStatus {
  Pending = "pending",
  Planning = "planning",
  Executing = "executing",
  WaitingApproval = "waiting_approval",
  Reflecting = "reflecting",
  Evaluating = "evaluating",
  Completed = "completed",
  Failed = "failed",
  Cancelled = "cancelled",
}

export interface Session {
  sessionId: string;
  runId: string;
  threadId: string;
  status: SessionStatus;
  stage: string;
  startedAt: string;
  updatedAt: string;
  progress: number;
  activeAgent: string;
  currentTask: string;
}

// Memory Models
export type MemoryType = "working" | "episodic" | "semantic" | "procedural";

export interface MemoryItem {
  id: string;
  type: MemoryType;
  content: string;
  context?: string;
  confidence: number;
  tags: string[];
  createdAt: string;
  associations?: string[];
}

// Knowledge Models
export interface KnowledgeDocument {
  id: string;
  title: string;
  snippet: string;
  source: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
}

// Governance Models
export type ApprovalStatus = "pending" | "approved" | "denied" | "expired" | "cancelled";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ApprovalRequest {
  id: string;
  resourceId: string;
  agentId: string;
  requestedAction: string;
  status: ApprovalStatus;
  riskLevel: RiskLevel;
  justification: string;
  requestedAt: string;
  expiresAt: string;
  resolvedAt?: string;
  resolvedBy?: string;
}

export interface GovernancePolicy {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
  riskThreshold: RiskLevel;
  createdAt: string;
  updatedAt: string;
}

export interface AuditRecord {
  id: string;
  action: string;
  actor: string;
  target: string;
  status: "success" | "failure" | "blocked";
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Metric {
  id: string;
  name: string;
  value: number;
  timestamp: string;
}
