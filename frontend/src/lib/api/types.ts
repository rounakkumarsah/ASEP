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
  associations?: string[]; // IDs of related memories or knowledge
}

// Knowledge Models
export interface KnowledgeDocument {
  id: string;
  title: string;
  snippet: string;
  source: string; // e.g., "Documentation", "API Spec", "User Upload"
  createdAt: string;
  updatedAt: string;
  tags: string[];
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
