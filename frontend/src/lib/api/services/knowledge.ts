import { ApiResponse, KnowledgeDocument, PaginatedResponse } from "../types";

// Mock data for knowledge base
const mockKnowledge: KnowledgeDocument[] = [
  {
    id: "doc_k_01",
    title: "Authentication Protocol v2",
    snippet: "The v2 protocol requires RS256 signing for all JWT tokens issued by the core auth service. Refresh tokens are valid for 7 days.",
    source: "Architecture Guidelines",
    tags: ["auth", "security", "jwt", "architecture"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(),
  },
  {
    id: "doc_k_02",
    title: "Deployment Strategy: Kubernetes",
    snippet: "All agent microservices must define resource limits. Specifically, CPU limits should be set to 500m and Memory to 1Gi.",
    source: "DevOps Runbook",
    tags: ["kubernetes", "devops", "deployment"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 120).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
  },
  {
    id: "doc_k_03",
    title: "Agent Prompt Injection Mitigation",
    snippet: "User inputs must be sanitized through the primary LLM firewall before being passed to the executor agent. Disallow standard system overrides.",
    source: "Security Policy",
    tags: ["security", "llm", "prompts"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
  }
];

export const knowledgeService = {
  async getDocuments(query?: string): Promise<ApiResponse<PaginatedResponse<KnowledgeDocument>>> {
    // const response = await apiClient.get('/api/v1/knowledge/documents', { params: { query } });
    // return response.data;
    
    return new Promise((resolve) => {
      setTimeout(() => {
        let filtered = mockKnowledge;
        if (query) {
          const lowerQuery = query.toLowerCase();
          filtered = filtered.filter(d => 
            d.title.toLowerCase().includes(lowerQuery) || 
            d.snippet.toLowerCase().includes(lowerQuery) ||
            d.tags.some(t => t.toLowerCase().includes(lowerQuery))
          );
        }
        resolve({
          status: "success",
          data: {
            items: filtered,
            total: filtered.length,
            page: 1,
            size: 50,
            pages: 1
          }
        });
      }, 400); // Simulate network
    });
  }
};
