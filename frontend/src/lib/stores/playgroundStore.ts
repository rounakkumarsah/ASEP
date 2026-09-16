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

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  attachments?: Attachment[];
}

export interface PlaygroundState {
  // Model Settings
  model: string;
  setModel: (model: string) => void;
  temperature: number;
  setTemperature: (temp: number) => void;
  maxTokens: number;
  setMaxTokens: (tokens: number) => void;

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
  terminalLogs: { id: string; type: "input" | "output" | "error" | "system" | "success" | "agent"; text: string; time?: string }[];
  addTerminalLog: (type: "input" | "output" | "error" | "system" | "success" | "agent", text: string) => void;
  clearTerminalLogs: () => void;

  // GitHub Repo State
  githubRepo: { url: string; files: string[]; activeFile: string | null } | null;
  setGithubRepo: (repo: { url: string; files: string[]; activeFile: string | null } | null) => void;
  setGithubActiveFile: (file: string | null) => void;

  // Metrics
  sessionMetrics: { estimatedCost: number | null; confidence: number | null } | null;
  setSessionMetrics: (metrics: { estimatedCost: number | null; confidence: number | null } | null) => void;
}

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

      terminalLogs: [
        { id: "init-1", type: "system", text: "ASEP AI Engine v0.1.0 (x86_64-pc-linux-gnu)" },
        { id: "init-2", type: "system", text: "Type 'help' to view available commands, or 'run <task>' to dispatch agents." },
        { id: "init-3", type: "input", text: "agent-cli run --mode=deep --workspace=default" },
        { id: "init-4", type: "output", text: "Initializing LangGraph multi-agent supervisor..." },
        { id: "init-5", type: "success", text: "[OK] Agent Swarm ready. Interactive session established." },
      ],
      addTerminalLog: (type, text) => set((state) => ({
        terminalLogs: [...state.terminalLogs, { id: Math.random().toString(), type, text, time: new Date().toLocaleTimeString() }]
      })),
      clearTerminalLogs: () => set({ terminalLogs: [] }),

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
      }),
    }
  )
);
