import {
  ApiResponse,
  MemoryItem,
  MemoryType,
  PaginatedResponse,
} from "../types";

// Mock data for memories
const mockMemories: MemoryItem[] = [
  {
    id: "mem_w_01",
    type: "working",
    content:
      "Currently evaluating API rate limit constraints for the stripe integration module.",
    context: "Session sess_01H1",
    confidence: 0.95,
    tags: ["stripe", "rate-limits", "api"],
    createdAt: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
  },
  {
    id: "mem_e_01",
    type: "episodic",
    content:
      "Failed to deploy the authentication microservice due to missing JWT_SECRET in the staging environment.",
    context: "Run run_alpha_99",
    confidence: 1.0,
    tags: ["deployment", "auth", "error", "staging"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    associations: ["doc_k_05"],
  },
  {
    id: "mem_s_01",
    type: "semantic",
    content:
      "The company's standard color palette uses primary brand color #0F172A (slate-900).",
    confidence: 0.88,
    tags: ["design", "branding", "css"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 15).toISOString(),
  },
  {
    id: "mem_p_01",
    type: "procedural",
    content:
      "When generating a new React component, always use a named export and include a strict TypeScript interface for props.",
    confidence: 0.99,
    tags: ["react", "typescript", "conventions"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
  },
  {
    id: "mem_w_02",
    type: "working",
    content:
      "Holding the temporary file path for the image upload processing step: /tmp/upload_992.png",
    context: "Session sess_01H2",
    confidence: 0.9,
    tags: ["upload", "temp"],
    createdAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
  },
];

export const memoryService = {
  async getMemories(
    type?: MemoryType,
    query?: string,
  ): Promise<ApiResponse<PaginatedResponse<MemoryItem>>> {
    // const response = await apiClient.get('/api/v1/memory', { params: { type, query } });
    // return response.data;

    return new Promise((resolve) => {
      setTimeout(() => {
        let filtered = mockMemories;
        if (type) {
          filtered = filtered.filter((m) => m.type === type);
        }
        if (query) {
          const lowerQuery = query.toLowerCase();
          filtered = filtered.filter(
            (m) =>
              m.content.toLowerCase().includes(lowerQuery) ||
              m.tags.some((t) => t.toLowerCase().includes(lowerQuery)),
          );
        }
        resolve({
          status: "success",
          data: {
            items: filtered,
            total: filtered.length,
            page: 1,
            size: 50,
            pages: 1,
          },
        });
      }, 400); // Simulate network
    });
  },
};
