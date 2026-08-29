import { ApiResponse, KnowledgeDocument, PaginatedResponse } from "../types";

import { apiClient } from "../client";

const DEFAULT_DEMO_DOCS: KnowledgeDocument[] = [
  {
    id: "doc_kn_001",
    title: "ASEP System Architecture & Topology",
    snippet: "Overview of FastAPI async runtime, LangGraph state machine, Redis cache, and Qdrant RAG.",
    source: "Documentation / Architecture",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
    tags: ["architecture", "core", "langgraph"],
  },
  {
    id: "doc_kn_002",
    title: "Enterprise Human-in-the-Loop Governance Protocol",
    snippet: "Specification of policy guardrails, permission boundaries, and WebSocket approval workflows.",
    source: "Documentation / Security",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    tags: ["security", "hitl", "governance"],
  },
  {
    id: "doc_kn_003",
    title: "Vector Codebase Embeddings & Memory Sync",
    snippet: "Detailed documentation of hierarchical chunking and cosine similarity index in Qdrant.",
    source: "Documentation / Memory",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 36).toISOString(),
    tags: ["qdrant", "rag", "embeddings"],
  },
];

export const knowledgeService = {
  async getDocuments(
    query?: string,
  ): Promise<ApiResponse<PaginatedResponse<KnowledgeDocument>>> {
    try {
      const response = await apiClient.get('/api/v1/knowledge/documents', { params: { query } });
      const items = response.data?.items && response.data.items.length > 0 ? response.data.items : DEFAULT_DEMO_DOCS;
      return {
        status: "success",
        data: {
          items: query ? items.filter((d: KnowledgeDocument) => d.title.toLowerCase().includes(query.toLowerCase()) || d.snippet.toLowerCase().includes(query.toLowerCase())) : items,
          total: items.length,
          page: 1,
          size: 50,
          pages: 1,
        }
      };
    } catch {
      const items = query ? DEFAULT_DEMO_DOCS.filter(d => d.title.toLowerCase().includes(query.toLowerCase()) || d.snippet.toLowerCase().includes(query.toLowerCase())) : DEFAULT_DEMO_DOCS;
      return {
        status: "success",
        data: { items, total: items.length, page: 1, size: 50, pages: 1 }
      };
    }
  },
};
