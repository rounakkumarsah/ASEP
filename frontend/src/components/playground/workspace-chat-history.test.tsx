import { describe, it, expect, beforeEach } from 'vitest';
import { useWorkspaceStore } from '@/lib/stores/workspaceStore';
import { useChatHistoryStore } from '@/lib/stores/chatHistoryStore';

describe('Workspace and Chat History System', () => {
  beforeEach(() => {
    // Reset workspace store to initial state
    useWorkspaceStore.setState({
      workspaces: [
        {
          id: 'ws_default',
          name: "Sachin's Workspace",
          slug: 'sachins-workspace',
          description: 'Primary engineering and agent workspace',
          isDefault: true,
          createdAt: new Date().toISOString(),
        },
      ],
      activeWorkspaceId: 'ws_default',
    });

    // Reset chat history store
    useChatHistoryStore.setState({
      sessions: [],
      activeSessionId: null,
    });
  });

  describe('useWorkspaceStore', () => {
    it('initializes with default workspace', () => {
      const active = useWorkspaceStore.getState().getActiveWorkspace();
      expect(active).toBeDefined();
      expect(active.name).toBe("Sachin's Workspace");
      expect(active.id).toBe('ws_default');
    });

    it('creates a new workspace and makes it active', () => {
      const store = useWorkspaceStore.getState();
      const newWs = store.createWorkspace('AI Research Lab', 'Exploration of LLM agents');

      expect(newWs.id).toBeDefined();
      expect(newWs.name).toBe('AI Research Lab');
      expect(newWs.slug).toBe('ai-research-lab');
      expect(newWs.description).toBe('Exploration of LLM agents');

      const state = useWorkspaceStore.getState();
      expect(state.workspaces.length).toBe(2);
      expect(state.activeWorkspaceId).toBe(newWs.id);
      expect(state.getActiveWorkspace().name).toBe('AI Research Lab');
    });

    it('switches between existing workspaces', () => {
      const store = useWorkspaceStore.getState();
      const ws2 = store.createWorkspace('Client Alpha');

      expect(useWorkspaceStore.getState().activeWorkspaceId).toBe(ws2.id);

      useWorkspaceStore.getState().switchWorkspace('ws_default');
      expect(useWorkspaceStore.getState().activeWorkspaceId).toBe('ws_default');
      expect(useWorkspaceStore.getState().getActiveWorkspace().name).toBe("Sachin's Workspace");
    });

    it('renames a workspace', () => {
      const store = useWorkspaceStore.getState();
      store.renameWorkspace('ws_default', 'Sachin Global HQ');

      const updated = useWorkspaceStore.getState().getActiveWorkspace();
      expect(updated.name).toBe('Sachin Global HQ');
    });

    it('prevents deletion of default workspace', () => {
      const store = useWorkspaceStore.getState();
      store.deleteWorkspace('ws_default');

      expect(useWorkspaceStore.getState().workspaces.length).toBe(1);
      expect(useWorkspaceStore.getState().activeWorkspaceId).toBe('ws_default');
    });
  });

  describe('useChatHistoryStore', () => {
    it('creates a new chat session and sets it as active', () => {
      const store = useChatHistoryStore.getState();
      const session = store.createSession({
        projectId: 'prj_1',
        projectName: 'ASEP Platform',
        workspaceId: 'ws_default',
        workspaceName: "Sachin's Workspace",
      });

      expect(session.id).toBeDefined();
      expect(session.title).toBe('New Chat');
      expect(session.projectId).toBe('prj_1');
      expect(session.projectName).toBe('ASEP Platform');

      const state = useChatHistoryStore.getState();
      expect(state.sessions.length).toBe(1);
      expect(state.activeSessionId).toBe(session.id);
    });

    it('saves and updates session with auto-generated title from first user message', () => {
      const store = useChatHistoryStore.getState();
      const session = store.createSession();

      const updated = store.saveOrUpdateSession({
        id: session.id,
        messages: [
          { role: 'user', content: 'Design a high-throughput payment processing architecture', timestamp: '12:00 PM' },
          { role: 'assistant', content: 'Here is the architecture using Kafka and Postgres...', timestamp: '12:01 PM' },
        ],
        projectName: 'Payments API',
      });

      expect(updated.title).toBe('Design a high-throughput payment processing a...');
      expect(updated.messageCount).toBe(2);
      expect(updated.projectName).toBe('Payments API');
      expect(updated.lastMessageSnippet).toContain('Here is the architecture');
    });

    it('renames a chat session', () => {
      const store = useChatHistoryStore.getState();
      const session = store.createSession();
      store.renameSession(session.id, 'Payment System Architecture Refactor');

      const found = useChatHistoryStore.getState().getSession(session.id);
      expect(found?.title).toBe('Payment System Architecture Refactor');
    });

    it('deletes a chat session', () => {
      const store = useChatHistoryStore.getState();
      const s1 = store.createSession();
      const s2 = store.createSession();

      expect(useChatHistoryStore.getState().sessions.length).toBe(2);

      store.deleteSession(s1.id);
      expect(useChatHistoryStore.getState().sessions.length).toBe(1);
      expect(useChatHistoryStore.getState().getSession(s1.id)).toBeUndefined();
      expect(useChatHistoryStore.getState().getSession(s2.id)).toBeDefined();
    });

    it('clears all chat sessions', () => {
      const store = useChatHistoryStore.getState();
      store.createSession();
      store.createSession();

      expect(useChatHistoryStore.getState().sessions.length).toBe(2);

      store.clearAllSessions();
      expect(useChatHistoryStore.getState().sessions.length).toBe(0);
      expect(useChatHistoryStore.getState().activeSessionId).toBeNull();
    });
  });
});
