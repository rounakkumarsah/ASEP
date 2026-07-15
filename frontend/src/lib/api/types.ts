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

// Common Domain Models (Placeholders for now)

export interface Project {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

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

export interface Metric {
  id: string;
  name: string;
  value: number;
  timestamp: string;
}
