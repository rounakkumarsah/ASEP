import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Message } from "./playgroundStore";

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
  messageCount: number;
  projectId: string | null;
  projectName: string | null;
  workspaceId: string | null;
  workspaceName: string | null;
  lastMessageSnippet: string;
}

interface ChatHistoryState {
  sessions: ChatSession[];
  activeSessionId: string | null;

  // Actions
  setActiveSessionId: (id: string | null) => void;
  saveOrUpdateSession: (data: {
    id: string;
    title?: string;
    messages: Message[];
    projectId?: string | null;
    projectName?: string | null;
    workspaceId?: string | null;
    workspaceName?: string | null;
  }) => ChatSession;
  createSession: (params?: {
    projectId?: string | null;
    projectName?: string | null;
    workspaceId?: string | null;
    workspaceName?: string | null;
  }) => ChatSession;
  deleteSession: (id: string) => void;
  renameSession: (id: string, newTitle: string) => void;
  clearAllSessions: () => void;
  getSession: (id: string) => ChatSession | undefined;
}

export const useChatHistoryStore = create<ChatHistoryState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,

      setActiveSessionId: (id) => set({ activeSessionId: id }),

      saveOrUpdateSession: ({
        id,
        title,
        messages,
        projectId = null,
        projectName = null,
        workspaceId = null,
        workspaceName = null,
      }) => {
        const state = get();
        const existingIdx = state.sessions.findIndex((s) => s.id === id);

        const lastMessage = messages[messages.length - 1];
        const snippet = lastMessage
          ? lastMessage.content.slice(0, 100).replace(/\n/g, " ")
          : "Empty conversation";

        // Auto-generate title from first user message if not explicitly set
        const firstUserMsg = messages.find((m) => m.role === "user");
        const defaultTitle =
          firstUserMsg && firstUserMsg.content.trim()
            ? firstUserMsg.content.trim().slice(0, 45) + (firstUserMsg.content.trim().length > 45 ? "..." : "")
            : "New Chat";

        const existingTitle = existingIdx >= 0 ? state.sessions[existingIdx].title : "";
        const isPlaceholder = !existingTitle || existingTitle === "New Chat";
        const resolvedTitle = title?.trim() || (!isPlaceholder ? existingTitle : defaultTitle);

        const now = new Date().toISOString();

        if (existingIdx >= 0) {
          const updated: ChatSession = {
            ...state.sessions[existingIdx],
            title: resolvedTitle,
            updatedAt: now,
            messages,
            messageCount: messages.length,
            projectId: projectId ?? state.sessions[existingIdx].projectId,
            projectName: projectName ?? state.sessions[existingIdx].projectName,
            workspaceId: workspaceId ?? state.sessions[existingIdx].workspaceId,
            workspaceName: workspaceName ?? state.sessions[existingIdx].workspaceName,
            lastMessageSnippet: snippet,
          };

          const newSessions = [...state.sessions];
          newSessions[existingIdx] = updated;
          // Sort by updatedAt descending
          newSessions.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());

          set({ sessions: newSessions });
          return updated;
        } else {
          const newSession: ChatSession = {
            id,
            title: resolvedTitle,
            createdAt: now,
            updatedAt: now,
            messages,
            messageCount: messages.length,
            projectId,
            projectName,
            workspaceId,
            workspaceName,
            lastMessageSnippet: snippet,
          };

          const newSessions = [newSession, ...state.sessions];
          set({
            sessions: newSessions,
            activeSessionId: id,
          });
          return newSession;
        }
      },

      createSession: (params) => {
        const id = `chat_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
        const now = new Date().toISOString();
        const newSession: ChatSession = {
          id,
          title: "New Chat",
          createdAt: now,
          updatedAt: now,
          messages: [],
          messageCount: 0,
          projectId: params?.projectId || null,
          projectName: params?.projectName || null,
          workspaceId: params?.workspaceId || null,
          workspaceName: params?.workspaceName || null,
          lastMessageSnippet: "No messages yet",
        };

        set((state) => ({
          sessions: [newSession, ...state.sessions],
          activeSessionId: id,
        }));

        return newSession;
      },

      deleteSession: (id) => {
        set((state) => {
          const filtered = state.sessions.filter((s) => s.id !== id);
          const nextActive = state.activeSessionId === id ? (filtered[0]?.id || null) : state.activeSessionId;
          return {
            sessions: filtered,
            activeSessionId: nextActive,
          };
        });
      },

      renameSession: (id, newTitle) => {
        const clean = newTitle.trim();
        if (!clean) return;
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, title: clean, updatedAt: new Date().toISOString() } : s
          ),
        }));
      },

      clearAllSessions: () => {
        set({ sessions: [], activeSessionId: null });
      },

      getSession: (id) => {
        return get().sessions.find((s) => s.id === id);
      },
    }),
    {
      name: "asep_chat_history_storage_v1",
    }
  )
);
