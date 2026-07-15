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

export interface Session {
  id: string;
  projectId: string;
  status: "active" | "completed" | "failed";
  startedAt: string;
  endedAt?: string;
}

export interface Metric {
  id: string;
  name: string;
  value: number;
  timestamp: string;
}
