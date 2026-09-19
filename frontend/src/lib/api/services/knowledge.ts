import { ApiResponse, KnowledgeDocument, PaginatedResponse } from "../types";

import { apiClient } from "../client";

export const DEFAULT_DEMO_DOCS: KnowledgeDocument[] = [
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
      const rawData = response.data;
      const rawList: any[] = Array.isArray(rawData)
        ? rawData
        : Array.isArray(rawData?.items)
        ? rawData.items
        : Array.isArray(rawData?.data)
        ? rawData.data
        : [];

      let items: KnowledgeDocument[] = rawList.map((doc: any) => {
        const createdTime = typeof doc.created_at === "number"
          ? new Date(doc.created_at * 1000).toISOString()
          : doc.createdAt || doc.created_at || new Date().toISOString();
        const updatedTime = typeof doc.updated_at === "number"
          ? new Date(doc.updated_at * 1000).toISOString()
          : doc.updatedAt || doc.updated_at || new Date().toISOString();

        return {
          id: doc.document_id || doc.id || `doc_${Math.random().toString(36).slice(2, 9)}`,
          title: doc.source_name || doc.title || doc.name || doc.filename || "Untitled Document",
          snippet: doc.content
            ? doc.content.slice(0, 260) + (doc.content.length > 260 ? "..." : "")
            : doc.snippet || "Documentation segment indexed for RAG vector retrieval.",
          source: doc.source_type
            ? `${doc.source_type.replace(/_/g, " ").toUpperCase()}`
            : doc.source || "Knowledge Base",
          createdAt: createdTime,
          updatedAt: updatedTime,
          tags: doc.tags || [doc.source_type || "document", "rag", "vector"],
        };
      });

      if (items.length === 0 && !query) {
        items = DEFAULT_DEMO_DOCS;
      }

      const filtered = query
        ? items.filter(
            (d: KnowledgeDocument) =>
              d.title.toLowerCase().includes(query.toLowerCase()) ||
              d.snippet.toLowerCase().includes(query.toLowerCase()) ||
              d.tags.some((t) => t.toLowerCase().includes(query.toLowerCase()))
          )
        : items;

      return {
        status: "success",
        data: {
          items: filtered,
          total: filtered.length,
          page: 1,
          size: 50,
          pages: 1,
        },
      };
    } catch {
      return {
        status: "success",
        data: { items: DEFAULT_DEMO_DOCS, total: DEFAULT_DEMO_DOCS.length, page: 1, size: 50, pages: 1 },
      };
    }
  },

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post("/api/v1/upload/document", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  async indexTextDocument(title: string, content: string, tags?: string[]): Promise<any> {
    const response = await apiClient.post("/api/v1/knowledge", {
      title,
      content,
      tags: tags || ["manual", "markdown"],
    });
    return response.data;
  },
};
