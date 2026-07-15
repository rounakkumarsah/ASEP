import { ApiResponse, Session, SessionStatus } from "../types";

// Mock data for sessions
const mockSessions: Session[] = [
  {
    sessionId: "sess_01H1",
    runId: "run_alpha_99",
    threadId: "th_882",
    status: SessionStatus.Executing,
    stage: "Data Extraction",
    startedAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    updatedAt: new Date().toISOString(),
    progress: 45,
    activeAgent: "ResearchAgent",
    currentTask: "Scraping competitor pricing from top 5 domains",
  },
  {
    sessionId: "sess_01H2",
    runId: "run_beta_10",
    threadId: "th_883",
    status: SessionStatus.WaitingApproval,
    stage: "Deployment",
    startedAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    progress: 90,
    activeAgent: "DeployAgent",
    currentTask: "Waiting for human approval to push to production",
  },
  {
    sessionId: "sess_01H3",
    runId: "run_gamma_05",
    threadId: "th_884",
    status: SessionStatus.Completed,
    stage: "Finalization",
    startedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 1).toISOString(),
    progress: 100,
    activeAgent: "SupervisorAgent",
    currentTask: "Run finished successfully",
  }
];

export const sessionsService = {
  async getSessions(): Promise<ApiResponse<Session[]>> {
    // In Phase 3C.4, we mock this network call for the UI
    // const response = await apiClient.get('/api/v1/sessions');
    // return response.data;
    
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: "success",
          data: mockSessions
        });
      }, 500); // simulate network latency
    });
  },

  async getSession(id: string): Promise<ApiResponse<Session>> {
    // const response = await apiClient.get(`/api/v1/sessions/${id}`);
    // return response.data;

    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const session = mockSessions.find(s => s.sessionId === id);
        if (session) {
          resolve({
            status: "success",
            data: session
          });
        } else {
          reject(new Error("Session not found"));
        }
      }, 500);
    });
  }
};
