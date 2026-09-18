import { create } from 'zustand';

export interface Attachment {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
  extractedText?: string;
  isImage?: boolean;
}

export interface GitHubUser {
  username: string;
  avatar_url: string;
  email?: string | null;
  scopes: string[];
}

export type GitHubSyncStatus = 'idle' | 'synced' | 'behind' | 'conflict';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  attachments?: Attachment[];
}

export interface TerminalLogItem {
  id: string;
  type: "input" | "output" | "error" | "system" | "success" | "agent";
  text: string;
  time?: string;
}

export interface TerminalSession {
  id: string;
  title: string;
  logs: TerminalLogItem[];
  history: string[];
}

export interface PlaygroundState {
  // Model Settings
  model: string;
  setModel: (model: string) => void;
  temperature: number;
  setTemperature: (temp: number) => void;
  maxTokens: number;
  setMaxTokens: (tokens: number) => void;

  // Environment Mode
  environmentMode: "local" | "deploy";
  setEnvironmentMode: (mode: "local" | "deploy") => void;
  localSecrets: string[];
  setLocalSecrets: (secrets: string[] | Record<string, string>) => void;
  credentialsStatus: Record<string, string | boolean>;
  setCredentialsStatus: (status: Record<string, string | boolean>) => void;

  // System Prompt
  systemPrompt: string;
  setSystemPrompt: (prompt: string) => void;

  // Tools & Rules
  activeTools: string[];
  toggleTool: (tool: string) => void;
  researchMode: string;
  setResearchMode: (mode: string) => void;

  // Chat
  messages: Message[];
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void;
  addMessage: (message: Message) => void;
  attachments: Attachment[];
  setAttachments: (attachments: Attachment[] | ((prev: Attachment[]) => Attachment[])) => void;

  // Project
  selectedProjectId: string | null;
  selectedProjectName: string | null;
  setProject: (id: string | null, name: string | null) => void;

  // Layout State
  activeLeftTab: string;
  setActiveLeftTab: (tab: string) => void;
  activeCenterTab: string;
  setActiveCenterTab: (tab: string) => void;
  isThinking: boolean;
  setIsThinking: (thinking: boolean) => void;
  setSelectedProjectName: (name: string) => void;


  // Workflow Graph Live Execution State
  phaseMap: string[];
  setPhaseMap: (map: string[]) => void;
  activeNode: string | null;

  setActiveNode: (node: string | null) => void;
  completedNodes: string[];
  addCompletedNode: (node: string) => void;
  resetActiveNodes: () => void;

  // Terminal State
  terminalLogs: TerminalLogItem[];
  terminalSessions: TerminalSession[];
  activeTerminalSessionId: string;
  createTerminalSession: (title?: string) => string;
  closeTerminalSession: (id: string) => void;
  setActiveTerminalSessionId: (id: string) => void;
  refreshTerminalSession: (id?: string) => void;
  addTerminalLog: (type: "input" | "output" | "error" | "system" | "success" | "agent", text: string, sessionId?: string) => void;
  clearTerminalLogs: (sessionId?: string) => void;

  // GitHub Repo State
  githubRepo: { url: string; files: string[]; activeFile: string | null } | null;
  setGithubRepo: (repo: { url: string; files: string[]; activeFile: string | null } | null) => void;
  setGithubActiveFile: (file: string | null) => void;

  // Metrics
  sessionMetrics: { estimatedCost: number | null; confidence: number | null } | null;
  setSessionMetrics: (metrics: { estimatedCost: number | null; confidence: number | null } | null) => void;

  // Token Efficiency & Phase Budget Telemetry
  tokenUsagePerPhase: Record<string, number>;
  setTokenUsagePerPhase: (usage: Record<string, number> | ((prev: Record<string, number>) => Record<string, number>)) => void;
  tokenBudgets: Record<string, number>;
  setTokenBudgets: (budgets: Record<string, number>) => void;
  tokenSavings: { ast_slicing: number; diff_streaming: number; total_saved: number };
  setTokenSavings: (savings: { ast_slicing: number; diff_streaming: number; total_saved: number }) => void;
  budgetExceeded: { phase: string; prompt: string; used: number; budget: number; percent: number } | null;
  setBudgetExceeded: (info: { phase: string; prompt: string; used: number; budget: number; percent: number } | null) => void;

  // Host Manager — live app URL
  appUrl: string | null;
  setAppUrl: (url: string | null) => void;

  // GitHub Integration & Sync
  githubConnected: boolean;
  setGithubConnected: (connected: boolean) => void;
  githubUser: GitHubUser | null;
  setGithubUser: (user: GitHubUser | null) => void;
  githubSyncStatus: GitHubSyncStatus;
  setGithubSyncStatus: (status: GitHubSyncStatus) => void;
  githubLastSyncedSha: string | null;
  setGithubLastSyncedSha: (sha: string | null) => void;
  githubDiffs: Record<string, string>;
  setGithubDiffs: (diffs: Record<string, string>) => void;
  githubProposals: Record<string, string>;
  setGithubProposals: (proposals: Record<string, string>) => void;
  githubCommits: Record<string, string>;
  setGithubCommits: (commits: Record<string, string> | ((prev: Record<string, string>) => Record<string, string>)) => void;
  githubActiveRepo: string | null;
  setGithubActiveRepo: (repo: string | null) => void;
  githubActiveBranch: string | null;
  setGithubActiveBranch: (branch: string | null) => void;

  // Skills System
  activeSkills: string[];
  setActiveSkills: (skills: string[]) => void;
  skillCitations: string[];
  setSkillCitations: (citations: string[]) => void;

  // Live Exploration Feed
  explorationEvents: ExploreEvent[];
  addExplorationEvent: (event: ExploreEvent) => void;
  setExplorationEvents: (events: ExploreEvent[]) => void;
  phaseExplorations: Record<string, ExplorationSummary>;
  setPhaseExploration: (phase: string, summary: ExplorationSummary) => void;
  activeRightTab: 'trace' | 'explore';
  setActiveRightTab: (tab: 'trace' | 'explore') => void;
}

export interface ExploreEvent {
  id: string;
  phase: string;
  type: "search" | "read" | "analyze" | "think" | "tool_call";
  detail: string;
  file?: string;
  duration_ms: number;
  timestamp: string;
  match_count?: number;
  size_bytes?: number;
  content_preview?: string;
  status: "running" | "completed" | "failed";
  error?: string;
  tool_args?: Record<string, unknown>;
}

export interface ExplorationSummary {
  phase: string;
  relevant_files: string[];
  architecture_understanding: string;
  risks_identified: string[];
  files_explored_count: number;
  searches_count: number;
  duration_ms: number;
  tokens_saved: number;
}

export const DEFAULT_PHASE_BUDGETS: Record<string, number> = {
  research: 1500,
  clarification_gate: 500,
  blueprint: 2000,
  scaffold: 2500,
  implement: 3500,
  test: 2000,
  security_audit: 1500,
  deploy_clarification_gate: 500,
  deploy: 1000,
  host_manager: 500,
};

import { persist } from 'zustand/middleware';

export const usePlaygroundStore = create<PlaygroundState>()(
  persist(
    (set) => ({
      model: 'gemini-flash-latest',
      setModel: (model) => set({ model }),
      temperature: 0.7,
      setTemperature: (temperature) => set({ temperature }),
      maxTokens: 2048,
      setMaxTokens: (maxTokens) => set({ maxTokens }),

      // Environment Mode
      environmentMode: "local",
      setEnvironmentMode: (mode) => set({ environmentMode: mode }),
      localSecrets: [],
      setLocalSecrets: (secrets) => set({ localSecrets: Array.isArray(secrets) ? secrets : Object.keys(secrets || {}) }),
      credentialsStatus: {},
      setCredentialsStatus: (status) => set({ credentialsStatus: status }),

      systemPrompt: 'You are an expert AI assistant.',
      setSystemPrompt: (systemPrompt) => set({ systemPrompt }),

      activeTools: ['web', 'docs'],
      toggleTool: (tool) =>
        set((state) => ({
          activeTools: state.activeTools.includes(tool)
            ? state.activeTools.filter((t) => t !== tool)
            : [...state.activeTools, tool],
        })),
      researchMode: 'balanced',
      setResearchMode: (researchMode) => set({ researchMode }),

      messages: [],
      setMessages: (messages) => set((state) => ({ messages: typeof messages === 'function' ? messages(state.messages) : messages })),
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      attachments: [],
      setAttachments: (attachments) => set((state) => ({ attachments: typeof attachments === 'function' ? attachments(state.attachments) : attachments })),

      selectedProjectId: null,
      selectedProjectName: null,
      setProject: (id, name) => set({ selectedProjectId: id, selectedProjectName: name }),

      activeLeftTab: 'model',
      setActiveLeftTab: (tab) => set({ activeLeftTab: tab }),
      activeCenterTab: 'chat',
      setActiveCenterTab: (tab) => set({ activeCenterTab: tab }),
      isThinking: false,
      setIsThinking: (thinking) => set({ isThinking: thinking }),

      setSelectedProjectName: (name) => set({ selectedProjectName: name }),

      phaseMap: [],
      setPhaseMap: (map) => set({ phaseMap: map }),

      activeNode: null,

      setActiveNode: (node) => set({ activeNode: node }),
      completedNodes: [],
      addCompletedNode: (node) =>
        set((state) => ({
          completedNodes: state.completedNodes.includes(node)
            ? state.completedNodes
            : [...state.completedNodes, node],
        })),
      resetActiveNodes: () => set({ activeNode: null, completedNodes: [] }),

      terminalSessions: [
        {
          id: "term-1",
          title: "1: agent-cli",
          logs: [
            { id: "init-1", type: "system", text: "ASEP AI Engine v0.1.0 (x86_64-pc-linux-gnu)" },
            { id: "init-2", type: "system", text: "Type 'help' to view available commands, or 'run <task>' to dispatch agents." },
            { id: "init-3", type: "input", text: "agent-cli run --mode=deep --workspace=default" },
            { id: "init-4", type: "output", text: "Initializing LangGraph multi-agent supervisor..." },
            { id: "init-5", type: "success", text: "[OK] Agent Swarm ready. Interactive session established." },
          ],
          history: ["agent-cli run --mode=deep --workspace=default"],
        }
      ],
      activeTerminalSessionId: "term-1",
      terminalLogs: [
        { id: "init-1", type: "system", text: "ASEP AI Engine v0.1.0 (x86_64-pc-linux-gnu)" },
        { id: "init-2", type: "system", text: "Type 'help' to view available commands, or 'run <task>' to dispatch agents." },
        { id: "init-3", type: "input", text: "agent-cli run --mode=deep --workspace=default" },
        { id: "init-4", type: "output", text: "Initializing LangGraph multi-agent supervisor..." },
        { id: "init-5", type: "success", text: "[OK] Agent Swarm ready. Interactive session established." },
      ],
      createTerminalSession: (title) => {
        const id = `term-${Date.now()}`;
        set((state) => {
          const sessionCount = state.terminalSessions.length + 1;
          const sessionTitle = title || `${sessionCount}: agent-cli`;
          const initialLogs: TerminalLogItem[] = [
            { id: `init-${id}-1`, type: "system", text: `ASEP AI Agent CLI — Terminal #${sessionCount} [${new Date().toLocaleTimeString()}]` },
            { id: `init-${id}-2`, type: "system", text: "Interactive REPL ready. Type 'help' for commands, 'refresh' to restart session." },
            { id: `init-${id}-3`, type: "success", text: "[OK] Isolated terminal session established." },
          ];
          const newSession: TerminalSession = {
            id,
            title: sessionTitle,
            logs: initialLogs,
            history: ["agent-cli run --mode=deep --workspace=default"],
          };
          return {
            terminalSessions: [...state.terminalSessions, newSession],
            activeTerminalSessionId: id,
            terminalLogs: initialLogs,
          };
        });
        return id;
      },
      closeTerminalSession: (id) => {
        set((state) => {
          if (state.terminalSessions.length <= 1) {
            const targetSession = state.terminalSessions[0];
            const refreshedLogs: TerminalLogItem[] = [
              { id: `term-reset-${Date.now()}`, type: "system", text: `ASEP Terminal reset at ${new Date().toLocaleTimeString()}` },
              { id: `term-reset-ok`, type: "success", text: "[OK] Ready for instructions." },
            ];
            return {
              terminalSessions: [{ ...targetSession, logs: refreshedLogs }],
              terminalLogs: refreshedLogs,
            };
          }
          const remaining = state.terminalSessions.filter((s) => s.id !== id);
          const nextActiveId = state.activeTerminalSessionId === id ? remaining[remaining.length - 1].id : state.activeTerminalSessionId;
          const nextActiveSession = remaining.find((s) => s.id === nextActiveId) || remaining[0];
          return {
            terminalSessions: remaining,
            activeTerminalSessionId: nextActiveId,
            terminalLogs: nextActiveSession.logs,
          };
        });
      },
      setActiveTerminalSessionId: (id) => {
        set((state) => {
          const target = state.terminalSessions.find((s) => s.id === id);
          if (!target) return state;
          return {
            activeTerminalSessionId: id,
            terminalLogs: target.logs,
          };
        });
      },
      refreshTerminalSession: (id) => {
        set((state) => {
          const targetId = id || state.activeTerminalSessionId || state.terminalSessions[0]?.id || "term-1";
          const timestamp = new Date().toLocaleTimeString();
          const refreshedLogs: TerminalLogItem[] = [
            { id: `ref-${Date.now()}-1`, type: "system", text: `[Terminal Refreshed] Environment re-initialized at ${timestamp}.` },
            { id: `ref-${Date.now()}-2`, type: "output", text: "Reloading agent supervisor and local execution context..." },
            { id: `ref-${Date.now()}-3`, type: "success", text: "[OK] Agent Swarm ready. Interactive session established." },
          ];
          const updatedSessions = state.terminalSessions.map((sess) => {
            if (sess.id === targetId) {
              return { ...sess, logs: refreshedLogs };
            }
            return sess;
          });
          return {
            terminalSessions: updatedSessions,
            terminalLogs: targetId === state.activeTerminalSessionId ? refreshedLogs : state.terminalLogs,
          };
        });
      },
      addTerminalLog: (type, text, sessionId) => set((state) => {
        const newLog: TerminalLogItem = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          type,
          text,
          time: new Date().toLocaleTimeString(),
        };
        const targetId = sessionId || state.activeTerminalSessionId || state.terminalSessions[0]?.id || "term-1";
        const updatedSessions = state.terminalSessions.map((sess) => {
          if (sess.id === targetId) {
            return { ...sess, logs: [...sess.logs, newLog] };
          }
          return sess;
        });
        return {
          terminalSessions: updatedSessions,
          terminalLogs: targetId === state.activeTerminalSessionId ? [...state.terminalLogs, newLog] : state.terminalLogs,
        };
      }),
      clearTerminalLogs: (sessionId) => set((state) => {
        const targetId = sessionId || state.activeTerminalSessionId || state.terminalSessions[0]?.id || "term-1";
        const updatedSessions = state.terminalSessions.map((sess) => {
          if (sess.id === targetId) {
            return { ...sess, logs: [] };
          }
          return sess;
        });
        return {
          terminalSessions: updatedSessions,
          terminalLogs: targetId === state.activeTerminalSessionId ? [] : state.terminalLogs,
        };
      }),

      githubRepo: null,
      setGithubRepo: (githubRepo) => set({ githubRepo }),
      setGithubActiveFile: (activeFile) =>
        set((state) => ({
          githubRepo: state.githubRepo
            ? { ...state.githubRepo, activeFile }
            : null,
        })),

      sessionMetrics: null,
      setSessionMetrics: (sessionMetrics) => set({ sessionMetrics }),

      tokenUsagePerPhase: {},
      setTokenUsagePerPhase: (usage) =>
        set((state) => ({
          tokenUsagePerPhase: typeof usage === 'function' ? usage(state.tokenUsagePerPhase) : usage,
        })),
      tokenBudgets: DEFAULT_PHASE_BUDGETS,
      setTokenBudgets: (tokenBudgets) => set({ tokenBudgets }),
      tokenSavings: { ast_slicing: 0, diff_streaming: 0, total_saved: 0 },
      setTokenSavings: (tokenSavings) => set({ tokenSavings }),
      budgetExceeded: null,
      setBudgetExceeded: (budgetExceeded) => set({ budgetExceeded }),

      // Host Manager — live app URL
      appUrl: null,
      setAppUrl: (appUrl) => set({ appUrl }),

      // GitHub Integration & Sync
      githubConnected: false,
      setGithubConnected: (githubConnected) => set({ githubConnected }),
      githubUser: null,
      setGithubUser: (githubUser) => set({ githubUser }),
      githubSyncStatus: 'idle',
      setGithubSyncStatus: (githubSyncStatus) => set({ githubSyncStatus }),
      githubLastSyncedSha: null,
      setGithubLastSyncedSha: (githubLastSyncedSha) => set({ githubLastSyncedSha }),
      githubDiffs: {},
      setGithubDiffs: (githubDiffs) => set({ githubDiffs }),
      githubProposals: {},
      setGithubProposals: (githubProposals) => set({ githubProposals }),
      githubCommits: {},
      setGithubCommits: (commits) =>
        set((state) => ({
          githubCommits: typeof commits === 'function' ? commits(state.githubCommits) : commits,
        })),
      githubActiveRepo: null,
      setGithubActiveRepo: (githubActiveRepo) => set({ githubActiveRepo }),
      githubActiveBranch: null,
      setGithubActiveBranch: (githubActiveBranch) => set({ githubActiveBranch }),
      activeSkills: [],
      setActiveSkills: (activeSkills) => set({ activeSkills }),
      skillCitations: [],
      setSkillCitations: (skillCitations) => set({ skillCitations }),

      // Live Exploration Feed
      explorationEvents: [],
      addExplorationEvent: (event) =>
        set((state) => ({
          explorationEvents: [...state.explorationEvents, event].slice(-500),
        })),
      setExplorationEvents: (events) => set({ explorationEvents: events.slice(-500) }),
      phaseExplorations: {},
      setPhaseExploration: (phase, summary) =>
        set((state) => ({
          phaseExplorations: { ...state.phaseExplorations, [phase]: summary },
        })),
      activeRightTab: 'trace',
      setActiveRightTab: (activeRightTab) => set({ activeRightTab }),
    }),
    {
      name: 'asep-playground-storage',
      partialize: (state) => ({
        model: state.model,
        temperature: state.temperature,
        maxTokens: state.maxTokens,
        systemPrompt: state.systemPrompt,
        activeTools: state.activeTools,
        researchMode: state.researchMode,
        messages: state.messages,
        attachments: state.attachments,
        githubRepo: state.githubRepo,
        terminalLogs: state.terminalLogs,
        activeNode: state.activeNode,
        completedNodes: state.completedNodes,
        tokenUsagePerPhase: state.tokenUsagePerPhase,
        tokenBudgets: state.tokenBudgets,
        tokenSavings: state.tokenSavings,
        githubConnected: state.githubConnected,
        githubUser: state.githubUser,
        githubSyncStatus: state.githubSyncStatus,
        githubCommits: state.githubCommits,
        githubActiveRepo: state.githubActiveRepo,
        githubActiveBranch: state.githubActiveBranch,
        activeSkills: state.activeSkills,
        skillCitations: state.skillCitations,
        explorationEvents: state.explorationEvents,
        phaseExplorations: state.phaseExplorations,
        activeRightTab: state.activeRightTab,
      }),
    }
  )
);
