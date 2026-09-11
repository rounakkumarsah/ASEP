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
  role: 'user' | 'assistant';
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
}

export const usePlaygroundStore = create<PlaygroundState>((set) => ({
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
}));
