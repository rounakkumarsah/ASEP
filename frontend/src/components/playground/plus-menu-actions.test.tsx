import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AVAILABLE_MODELS, ALL_TOOLS } from './CenterWorkspace';
import { usePlaygroundStore, Attachment } from '@/lib/stores/playgroundStore';
import { useSidebarStore } from '@/lib/stores/sidebarStore';

describe('Playground Plus Menu Actions & Capabilities', () => {
  beforeEach(() => {
    // Reset stores
    usePlaygroundStore.setState({
      model: 'gemini-flash-latest',
      activeTools: ['web', 'docs'],
      attachments: [],
      messages: [],
      activeLeftTab: 'model',
    });
    useSidebarStore.setState({
      isLeftPanelOpen: false,
    });
  });

  describe('Plus Menu Model Options (AVAILABLE_MODELS)', () => {
    it('provides all expected multi-provider models including Gemini, Groq, Claude, OpenAI, and DeepSeek', () => {
      const modelIds = AVAILABLE_MODELS.map((m) => m.id);
      expect(modelIds).toContain('gemini-flash-latest');
      expect(modelIds).toContain('gemini-pro-latest');
      expect(modelIds).toContain('claude-3-5-sonnet-20240620');
      expect(modelIds).toContain('gpt-4o');
      expect(modelIds).toContain('deepseek-coder');
      expect(modelIds).toContain('llama-3.3-70b');
      expect(modelIds).toContain('auto-router');
    });

    it('each model entry contains valid metadata (id, name, provider, desc)', () => {
      AVAILABLE_MODELS.forEach((m) => {
        expect(m.id).toBeTruthy();
        expect(m.name).toBeTruthy();
        expect(m.provider).toBeTruthy();
        expect(m.desc).toBeTruthy();
      });
    });

    it('updates playground store model when a new model is selected', () => {
      const { setModel } = usePlaygroundStore.getState();
      
      setModel('llama-3.3-70b');
      expect(usePlaygroundStore.getState().model).toBe('llama-3.3-70b');

      setModel('claude-3-5-sonnet-20240620');
      expect(usePlaygroundStore.getState().model).toBe('claude-3-5-sonnet-20240620');

      setModel('auto-router');
      expect(usePlaygroundStore.getState().model).toBe('auto-router');
    });
  });

  describe('Plus Menu Tool Options (ALL_TOOLS)', () => {
    it('defines all core tools: web search, official docs, github repos, python sandbox', () => {
      const toolIds = ALL_TOOLS.map((t) => t.id);
      expect(toolIds).toContain('web');
      expect(toolIds).toContain('docs');
      expect(toolIds).toContain('github');
      expect(toolIds).toContain('sandbox');
    });

    it('allows toggling tools in playground store', () => {
      const { toggleTool } = usePlaygroundStore.getState();
      
      // Default active: ['web', 'docs']
      expect(usePlaygroundStore.getState().activeTools).toEqual(['web', 'docs']);

      // Toggle github on
      toggleTool('github');
      expect(usePlaygroundStore.getState().activeTools).toContain('github');

      // Toggle web off
      toggleTool('web');
      expect(usePlaygroundStore.getState().activeTools).not.toContain('web');

      // Toggle sandbox on
      toggleTool('sandbox');
      expect(usePlaygroundStore.getState().activeTools).toContain('sandbox');
    });

    it('supports opening tools tab in left panel via sidebar store and playground store', () => {
      const { setLeftPanelOpen } = useSidebarStore.getState();
      const { setActiveLeftTab } = usePlaygroundStore.getState();

      expect(useSidebarStore.getState().isLeftPanelOpen).toBe(false);

      // Simulating Manage Tools action: opens panel and activates tools tab
      setLeftPanelOpen(true);
      setActiveLeftTab('tools');

      expect(useSidebarStore.getState().isLeftPanelOpen).toBe(true);
      expect(usePlaygroundStore.getState().activeLeftTab).toBe('tools');
    });
  });

  describe('Upload Media & File Attachments Workflow', () => {
    it('stores file attachments in playground store', () => {
      const { setAttachments } = usePlaygroundStore.getState();

      const mockAttachment: Attachment = {
        id: 'att-123',
        name: 'architecture_diagram.png',
        size: 1024 * 150, // 150 KB
        type: 'image/png',
        url: 'data:image/png;base64,mockImageData',
        isImage: true,
      };

      setAttachments([mockAttachment]);
      expect(usePlaygroundStore.getState().attachments).toHaveLength(1);
      expect(usePlaygroundStore.getState().attachments[0].name).toBe('architecture_diagram.png');
      expect(usePlaygroundStore.getState().attachments[0].isImage).toBe(true);
    });

    it('supports multiple file attachments including text and code files', () => {
      const { setAttachments } = usePlaygroundStore.getState();

      const imageAtt: Attachment = {
        id: 'att-1',
        name: 'screenshot.png',
        size: 50000,
        type: 'image/png',
        url: 'data:image/png;base64,img',
        isImage: true,
      };

      const codeAtt: Attachment = {
        id: 'att-2',
        name: 'service.py',
        size: 4200,
        type: 'text/x-python',
        extractedText: 'def process_data(): return True',
        isImage: false,
      };

      const pdfAtt: Attachment = {
        id: 'att-3',
        name: 'spec.pdf',
        size: 250000,
        type: 'application/pdf',
        url: 'data:application/pdf;base64,pdf',
        isImage: false,
      };

      setAttachments([imageAtt, codeAtt, pdfAtt]);
      const current = usePlaygroundStore.getState().attachments;
      expect(current).toHaveLength(3);
      expect(current[1].extractedText).toContain('def process_data()');
      expect(current[2].type).toBe('application/pdf');
    });

    it('allows removing an individual attachment by id', () => {
      const { setAttachments } = usePlaygroundStore.getState();

      setAttachments([
        { id: 'att-1', name: 'file1.txt', size: 100, type: 'text/plain', isImage: false },
        { id: 'att-2', name: 'file2.txt', size: 200, type: 'text/plain', isImage: false },
      ]);

      expect(usePlaygroundStore.getState().attachments).toHaveLength(2);

      // Remove att-1
      setAttachments((prev) => prev.filter((a) => a.id !== 'att-1'));
      expect(usePlaygroundStore.getState().attachments).toHaveLength(1);
      expect(usePlaygroundStore.getState().attachments[0].id).toBe('att-2');
    });

    it('allows clearing all attachments', () => {
      const { setAttachments } = usePlaygroundStore.getState();

      setAttachments([
        { id: 'att-1', name: 'file1.txt', size: 100, type: 'text/plain', isImage: false },
        { id: 'att-2', name: 'file2.txt', size: 200, type: 'text/plain', isImage: false },
      ]);

      setAttachments([]);
      expect(usePlaygroundStore.getState().attachments).toEqual([]);
    });

    it('attaches files to user message when sent and clears attachments', () => {
      const { setAttachments, addMessage } = usePlaygroundStore.getState();

      const testAtt: Attachment = {
        id: 'att-99',
        name: 'test.py',
        size: 512,
        type: 'text/plain',
        extractedText: 'print("hello")',
        isImage: false,
      };

      setAttachments([testAtt]);
      const currentAttachments = [...usePlaygroundStore.getState().attachments];

      addMessage({
        role: 'user',
        content: 'Please review this script',
        timestamp: '12:00 PM',
        attachments: currentAttachments,
      });
      setAttachments([]);

      const msgs = usePlaygroundStore.getState().messages;
      expect(msgs).toHaveLength(1);
      expect(msgs[0].content).toBe('Please review this script');
      expect(msgs[0].attachments).toHaveLength(1);
      expect(msgs[0].attachments?.[0].name).toBe('test.py');
      expect(usePlaygroundStore.getState().attachments).toHaveLength(0);
    });
  });
});
