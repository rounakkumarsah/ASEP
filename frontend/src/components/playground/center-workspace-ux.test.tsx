import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  classifyEvent,
  extractMessageContent,
  isStatusContent,
  processEventData,
  MessageItem,
  DEFAULT_MAIN_PY,
  DEFAULT_CONFIG_JSON,
  getLanguageFromFilename,
  getFileIconColor,
} from './CenterWorkspace';
import { usePlaygroundStore } from '@/lib/stores/playgroundStore';
import { apiClient } from '@/lib/api/client';

describe('CenterWorkspace UX - Event Classification, Extraction, and Message Routing', () => {
  describe('extractMessageContent()', () => {
    it('returns string as-is', () => {
      expect(extractMessageContent('Simple message')).toBe('Simple message');
    });

    it('extracts text from array of content blocks', () => {
      const content = [
        { type: 'text', text: 'Part 1' },
        { type: 'text', text: 'Part 2' },
      ];
      expect(extractMessageContent(content)).toBe('Part 1\nPart 2');
    });

    it('extracts text from object with text or content', () => {
      expect(extractMessageContent({ text: 'Object text' })).toBe('Object text');
      expect(extractMessageContent({ content: 'Object content' })).toBe('Object content');
    });

    it('returns empty string for null/undefined/empty', () => {
      expect(extractMessageContent(null)).toBe('');
      expect(extractMessageContent(undefined)).toBe('');
      expect(extractMessageContent('')).toBe('');
    });
  });

  describe('classifyEvent()', () => {
    it('classifies LangGraph execution initiation as STATUS', () => {
      const item: MessageItem = {
        role: 'system',
        content: 'LangGraph execution initiated for run 43818e69-9069-42b4-a4f1-93f0b2fbe0b3. Target objective: Build a react app',
      };
      expect(classifyEvent(item)).toBe('STATUS');
    });

    it('classifies phase start and complete events as STATUS', () => {
      expect(classifyEvent({ role: 'system', content: 'Phase started: planner' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Phase Complete: Capability Blueprint verified.' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Checkpoint saved: phase-1' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Blueprint Phase Complete: System design approved.' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Scaffold Phase Complete: Boilerplate generated.' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Implement Phase Complete: Core modules coded.' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Research Phase Complete: Loaded documentation.' })).toBe('STATUS');
    });

    it('classifies deployment gate and verification events as STATUS', () => {
      expect(classifyEvent({ role: 'system', content: 'Deploy Clarification Gate skipped in LOCAL mode.' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Critic Phase Complete: Sandbox execution verified successfully' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'Test Phase Complete: All units passed.' })).toBe('STATUS');
    });

    it('classifies AST, Diff, and Healing logs as STATUS', () => {
      expect(classifyEvent({ role: 'system', content: '[AST Slicer] Slicing affected functions' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: '[Diff Streamer] Unified diff emitted' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: 'heal cycle #2 starting...' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: '[Heal Cycle #1] Applying fix' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: '[Self-Healing Escalation] Max retry attempts exceeded.' })).toBe('STATUS');
    });

    it('classifies Exploration events and summaries as STATUS', () => {
      expect(classifyEvent({ role: 'system', content: '[Explore Event] {"query": "search"}' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: '[Explore Summary] {"phase": "explore"}' })).toBe('STATUS');
    });

    it('classifies tool messages as STATUS', () => {
      expect(classifyEvent({ type: 'tool', name: 'github', content: '{"success": true}' })).toBe('STATUS');
      expect(classifyEvent({ role: 'tool', name: 'bash', content: 'exit code 0' })).toBe('STATUS');
    });

    it('classifies real assistant LLM responses as FINAL_ANSWER', () => {
      const item: MessageItem = {
        role: 'assistant',
        content: 'I have implemented the requested authentication middleware in `src/auth.ts`.\n\n```typescript\nexport const auth = () => {};\n```',
      };
      expect(classifyEvent(item)).toBe('FINAL_ANSWER');
    });

    it('classifies ai role, model role, and ai type as FINAL_ANSWER', () => {
      expect(classifyEvent({ role: 'ai', content: 'Here is the generated schema.' })).toBe('FINAL_ANSWER');
      expect(classifyEvent({ role: 'model', content: 'Here is the Gemini model output.' })).toBe('FINAL_ANSWER');
      expect(classifyEvent({ type: 'ai', content: 'Here is the AI runnable message.' })).toBe('FINAL_ANSWER');
    });

    it('classifies multi-part array content as FINAL_ANSWER', () => {
      const item: MessageItem = {
        role: 'assistant',
        content: [
          { type: 'text', text: 'Here is step 1.' },
          { type: 'text', text: 'Here is step 2.' },
        ],
      };
      expect(classifyEvent(item)).toBe('FINAL_ANSWER');
    });

    it('classifies real assistant patch as FINAL_ANSWER', () => {
      const item: MessageItem = {
        role: 'assistant',
        content: '### Self-Healing Patch (Cycle #1)\n\n**Fix Summary:** Fixed import path\n\n```diff\n- import foo\n+ import bar\n```',
      };
      expect(classifyEvent(item)).toBe('FINAL_ANSWER');
    });

    it('classifies assistant messages that contain internal plumbing strings as STATUS', () => {
      // Even if role is accidentally 'assistant', plumbing text must never be classified as FINAL_ANSWER
      const item: MessageItem = {
        role: 'assistant',
        content: 'LangGraph execution initiated for run abc-123. Target objective: Do something',
      };
      expect(classifyEvent(item)).toBe('STATUS');
    });

    it('classifies empty or whitespace-only messages as STATUS', () => {
      expect(classifyEvent({ role: 'assistant', content: '' })).toBe('STATUS');
      expect(classifyEvent({ role: 'assistant', content: '   ' })).toBe('STATUS');
      expect(classifyEvent({ role: 'assistant' })).toBe('STATUS');
    });
  });

  describe('isStatusContent()', () => {
    it('returns true for all internal plumbing messages', () => {
      expect(isStatusContent('LangGraph execution initiated for run 123')).toBe(true);
      expect(isStatusContent('Phase started: coder')).toBe(true);
      expect(isStatusContent('Phase Complete: Tool Design verified.')).toBe(true);
      expect(isStatusContent('Blueprint Phase Complete: System design approved.')).toBe(true);
      expect(isStatusContent('Scaffold Phase Complete: Boilerplate generated.')).toBe(true);
      expect(isStatusContent('Implement Phase Complete: Core modules coded.')).toBe(true);
      expect(isStatusContent('Research Phase Complete: Loaded 10 chunks.')).toBe(true);
      expect(isStatusContent('Phase map generated: plan -> code -> test.')).toBe(true);
      expect(isStatusContent("Orchestrator classified product as 'web-app'. Phase map generated: plan -> code.")).toBe(true);
      expect(isStatusContent('Checkpoint saved: step-1')).toBe(true);
      expect(isStatusContent('[Token Budget Exceeded] Phase coder consumed 3000 tokens')).toBe(true);
      expect(isStatusContent('[Clarification Required] Please enter API key')).toBe(true);
      expect(isStatusContent('[Auto Router Toast] Switched to flash')).toBe(true);
      expect(isStatusContent('[Host Manager Status] [OK] Listening on http://localhost:3000')).toBe(true);
      expect(isStatusContent('Task processed through LangGraph multi-agent execution pipeline.')).toBe(true);
      expect(isStatusContent('Resumed execution.')).toBe(true);
      expect(isStatusContent('[Skill Activated] [SKILL: react]')).toBe(true);
      expect(isStatusContent('[Skill Reference] https://react.dev')).toBe(true);
      expect(isStatusContent('Security Audit Severity Table\n| Severity | Count |\n| Critical | 0 |')).toBe(true);
      expect(isStatusContent('### Security Audit: PASSED\n\nAll security policies passed.')).toBe(true);
    });

    it('returns false for actual LLM-generated answers and advice', () => {
      expect(isStatusContent('To solve this issue, we should configure CORS properly.')).toBe(false);
      expect(isStatusContent('```python\ndef hello():\n    return "world"\n```')).toBe(false);
      expect(isStatusContent('Here is the breakdown of the changes made to the database schema.')).toBe(false);
      expect(isStatusContent('### Self-Healing Patch (Cycle #1)\n\n**Fix Summary:** Fixed error')).toBe(false);
    });
  });

  describe('processEventData()', () => {
    it('extracts final answer from node updates with messages array', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();

      const eventData = {
        event: {
          coder: {
            messages: [
              { role: 'assistant', content: 'Here is your completed code.' },
            ],
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent });
      expect(onFinalAnswer).toHaveBeenCalledWith('Here is your completed code.');
      expect(onStatusEvent).not.toHaveBeenCalled();
    });

    it('extracts final answer from node updates with single message object', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();

      const eventData = {
        event: {
          coder: {
            message: { role: 'assistant', content: 'Single message object answer.' },
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent });
      expect(onFinalAnswer).toHaveBeenCalledWith('Single message object answer.');
    });

    it('extracts final answer from node updates with string content field', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();

      const eventData = {
        event: {
          coder: {
            content: 'Direct content string answer.',
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent });
      expect(onFinalAnswer).toHaveBeenCalledWith('Direct content string answer.');
    });

    it('extracts final answer from node updates with string message field', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();

      const eventData = {
        event: {
          coder: {
            message: 'Direct string message answer.',
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent });
      expect(onFinalAnswer).toHaveBeenCalledWith('Direct string message answer.');
    });

    it('routes telemetry and internal status in node updates to onStatusEvent, not onFinalAnswer', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();

      const eventData = {
        event: {
          orchestrator: {
            messages: [
              {
                role: 'system',
                content: 'LangGraph execution initiated for run abc-123. Target objective: Build app',
              },
              {
                role: 'system',
                content: 'Phase map generated: plan -> code -> test.',
              },
            ],
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent });
      expect(onFinalAnswer).not.toHaveBeenCalled();
      expect(onStatusEvent).toHaveBeenCalledTimes(2);
    });

    it('correctly handles mixed telemetry and final answer within the same node', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();

      const eventData = {
        event: {
          coder: {
            messages: [
              { role: 'system', content: '[Auto Router Toast] Switched to flash' },
              { role: 'assistant', content: 'Final code generated.' },
            ],
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent });
      expect(onStatusEvent).toHaveBeenCalledTimes(1);
      expect(onFinalAnswer).toHaveBeenCalledWith('Final code generated.');
    });

    it('extracts code blocks into onArtifactCode handler', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();
      const onArtifactCode = vi.fn();

      const eventData = {
        event: {
          implement: {
            messages: [
              {
                role: 'assistant',
                content: '```python\napp = FastAPI()\n```',
              },
            ],
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent, onArtifactCode });
      expect(onArtifactCode).toHaveBeenCalledWith('app = FastAPI()');
    });

    it('extracts direct generated_code field into onArtifactCode handler', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();
      const onArtifactCode = vi.fn();

      const eventData = {
        event: {
          implement: {
            generated_code: 'print("hello world")',
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent, onArtifactCode });
      expect(onArtifactCode).toHaveBeenCalledWith('print("hello world")');
    });

    it('extracts code blocks with CRLF line endings and trailing whitespace', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();
      const onArtifactCode = vi.fn();

      const eventData = {
        event: {
          implement: {
            messages: [
              {
                role: 'assistant',
                content: '```python  \r\ndef get_todos():\r\n    return []\r\n```',
              },
            ],
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent, onArtifactCode });
      expect(onArtifactCode).toHaveBeenCalledWith('def get_todos():\r\n    return []');
    });

    it('extracts code blocks without language specifier', () => {
      const onFinalAnswer = vi.fn();
      const onStatusEvent = vi.fn();
      const onArtifactCode = vi.fn();

      const eventData = {
        event: {
          implement: {
            messages: [
              {
                role: 'assistant',
                content: '```\nconst x = 42;\n```',
              },
            ],
          },
        },
      };

      processEventData(eventData, { onFinalAnswer, onStatusEvent, onArtifactCode });
      expect(onArtifactCode).toHaveBeenCalledWith('const x = 42;');
    });
  });

  describe('No Final Answer Fallback Rule', () => {
    it('uses the mandatory clean error message when no final answer event arrives', () => {
      const fallbackErrorMessage = 'The agent could not complete this task. Please try again.';
      const aiResponse: string = '';
      const finalAnswer = aiResponse && !isStatusContent(aiResponse) ? aiResponse.trim() : '';
      const finalContent = finalAnswer || fallbackErrorMessage;

      expect(finalContent).toBe('The agent could not complete this task. Please try again.');
      expect(finalContent).not.toContain('LangGraph');
      expect(finalContent).not.toContain('pipeline');
    });

    it('uses fallback error message even if aiResponse was accidentally set to status content', () => {
      const fallbackErrorMessage = 'The agent could not complete this task. Please try again.';
      const aiResponse: string = 'LangGraph execution initiated for run 123';
      const finalAnswer = aiResponse && !isStatusContent(aiResponse) ? aiResponse.trim() : '';
      const finalContent = finalAnswer || fallbackErrorMessage;

      expect(finalContent).toBe('The agent could not complete this task. Please try again.');
    });

    it('uses the real answer when clean aiResponse is present', () => {
      const fallbackErrorMessage = 'The agent could not complete this task. Please try again.';
      const aiResponse: string = 'Here is your solution.';
      const finalAnswer = aiResponse && !isStatusContent(aiResponse) ? aiResponse.trim() : '';
      const finalContent = finalAnswer || fallbackErrorMessage;

      expect(finalContent).toBe('Here is your solution.');
    });
  });

  describe('Artifacts Tab Templates & Background State Stability', () => {
    it('exports valid DEFAULT_MAIN_PY template containing FastAPI starter', () => {
      expect(DEFAULT_MAIN_PY).toBeDefined();
      expect(DEFAULT_MAIN_PY).toContain('main.py');
      expect(DEFAULT_MAIN_PY).toContain('FastAPI');
      expect(DEFAULT_MAIN_PY).toContain('@app.get');
    });

    it('exports valid DEFAULT_CONFIG_JSON template with proper json structure', () => {
      expect(DEFAULT_CONFIG_JSON).toBeDefined();
      const parsed = JSON.parse(DEFAULT_CONFIG_JSON);
      expect(parsed.name).toBe('todo-app');
      expect(parsed.main).toBe('main.py');
      expect(parsed.dependencies).toBeDefined();
      expect(parsed.dependencies.fastapi).toBeDefined();
    });

    it('processes telemetry and artifact code without mutating caller active tab state', () => {
      let activeTab = 'chat';
      const onArtifactCode = vi.fn((code: string) => {
        // Artifact code handler updates artifact code in store without switching tab
        expect(code).toBe('app = FastAPI()');
        expect(activeTab).toBe('chat');
      });

      const eventData = {
        event: {
          implement: {
            messages: [
              {
                role: 'assistant',
                content: '```python\napp = FastAPI()\n```',
              },
            ],
          },
        },
      };

      processEventData(eventData, { onArtifactCode });
      expect(onArtifactCode).toHaveBeenCalled();
      expect(activeTab).toBe('chat');
    });

    it('processes artifacts dictionary in event update and passes to onArtifacts handler', () => {
      const onArtifacts = vi.fn();
      const onArtifactCode = vi.fn();

      const eventData = {
        event: {
          scaffold: {
            artifacts: {
              'package.json': '{\n  "name": "my-app"\n}',
              'app/page.tsx': 'export default function Page() { return <div>Hello</div>; }',
            },
          },
        },
      };

      processEventData(eventData, { onArtifacts, onArtifactCode });
      expect(onArtifacts).toHaveBeenCalledWith({
        'package.json': '{\n  "name": "my-app"\n}',
        'app/page.tsx': 'export default function Page() { return <div>Hello</div>; }',
      });
      expect(onArtifactCode).toHaveBeenCalledWith('{\n  "name": "my-app"\n}');
    });
  });

  describe('Language & Icon Detection for Artifact Files', () => {
    it('maps file extensions to correct Monaco Editor languages', () => {
      expect(getLanguageFromFilename('app/page.tsx')).toBe('typescript');
      expect(getLanguageFromFilename('src/index.ts')).toBe('typescript');
      expect(getLanguageFromFilename('component.jsx')).toBe('javascript');
      expect(getLanguageFromFilename('index.js')).toBe('javascript');
      expect(getLanguageFromFilename('package.json')).toBe('json');
      expect(getLanguageFromFilename('main.py')).toBe('python');
      expect(getLanguageFromFilename('index.html')).toBe('html');
      expect(getLanguageFromFilename('styles.css')).toBe('css');
      expect(getLanguageFromFilename('README.md')).toBe('markdown');
      expect(getLanguageFromFilename('script.sh')).toBe('shell');
      expect(getLanguageFromFilename('docker-compose.yml')).toBe('yaml');
      expect(getLanguageFromFilename('Dockerfile')).toBe('dockerfile');
      expect(getLanguageFromFilename('Makefile')).toBe('makefile');
      expect(getLanguageFromFilename('.env')).toBe('ini');
      expect(getLanguageFromFilename('main.rs')).toBe('rust');
      expect(getLanguageFromFilename('server.go')).toBe('go');
      expect(getLanguageFromFilename('App.java')).toBe('java');
      expect(getLanguageFromFilename('query.sql')).toBe('sql');
      expect(getLanguageFromFilename('unknown.xyz')).toBe('plaintext');
      expect(getLanguageFromFilename('no_extension')).toBe('plaintext');
    });

    it('maps file extensions to appropriate icon color classes', () => {
      expect(getFileIconColor('main.py')).toBe('text-emerald-400');
      expect(getFileIconColor('config.json')).toBe('text-amber-400');
      expect(getFileIconColor('app/page.tsx')).toBe('text-cyan-400');
      expect(getFileIconColor('utils.js')).toBe('text-yellow-400');
      expect(getFileIconColor('style.css')).toBe('text-blue-400');
      expect(getFileIconColor('index.html')).toBe('text-orange-400');
      expect(getFileIconColor('README.md')).toBe('text-zinc-400');
      expect(getFileIconColor('main.go')).toBe('text-sky-400');
      expect(getFileIconColor('main.rs')).toBe('text-amber-600');
      expect(getFileIconColor('schema.sql')).toBe('text-indigo-400');
      expect(getFileIconColor('run.sh')).toBe('text-green-400');
      expect(getFileIconColor('docker-compose.yml')).toBe('text-rose-400');
      expect(getFileIconColor('file.unknown')).toBe('text-muted-foreground');
    });
  });

  describe('Backend Run Artifacts API Integration & Playground Store', () => {
    beforeEach(() => {
      usePlaygroundStore.setState({
        artifacts: {},
        selectedArtifactFile: null,
        activeRunId: null,
      });
      vi.restoreAllMocks();
    });

    it('fetches artifacts dictionary from GET /api/v1/conversations/run/{run_id}/artifacts and updates store', async () => {
      const mockRunId = 'run_abc_123';
      const mockArtifacts = {
        'package.json': '{\n  "name": "my-app"\n}',
        'app/page.tsx': 'export default function Page() { return <h1>ASEP</h1>; }',
      };

      const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: mockArtifacts,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await usePlaygroundStore.getState().fetchRunArtifacts(mockRunId);

      expect(getSpy).toHaveBeenCalledWith(`/api/v1/conversations/run/${mockRunId}/artifacts`);
      expect(result).toEqual(mockArtifacts);

      const state = usePlaygroundStore.getState();
      expect(state.artifacts).toEqual(mockArtifacts);
      expect(state.selectedArtifactFile).toBe('package.json');
    });

    it('normalizes Windows backslashes and leading slashes in artifact keys', async () => {
      const mockRunId = 'run_norm_123';
      const rawArtifacts = {
        'app\\page.tsx': 'export default function Page() {}',
        './package.json': '{"name": "test"}',
        '/src/index.ts': 'console.log("hello")',
      };

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: rawArtifacts,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await usePlaygroundStore.getState().fetchRunArtifacts(mockRunId);

      expect(result).toEqual({
        'app/page.tsx': 'export default function Page() {}',
        'package.json': '{"name": "test"}',
        'src/index.ts': 'console.log("hello")',
      });

      const state = usePlaygroundStore.getState();
      expect(Object.keys(state.artifacts)).toEqual(['app/page.tsx', 'package.json', 'src/index.ts']);
    });

    it('handles wrapped { artifacts: { ... } } responses from backend', async () => {
      const mockRunId = 'run_wrapped_456';
      const wrappedPayload = {
        artifacts: {
          'server.py': 'print("hello server")',
        },
      };

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: wrappedPayload,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await usePlaygroundStore.getState().fetchRunArtifacts(mockRunId);

      expect(result).toEqual({
        'server.py': 'print("hello server")',
      });
      expect(usePlaygroundStore.getState().artifacts).toEqual({
        'server.py': 'print("hello server")',
      });
    });

    it('sanitizes non-string artifact values safely into stringified format', async () => {
      const mockRunId = 'run_sanitize_789';
      const mixedPayload = {
        'config.json': { port: 8080, debug: true },
        'count.txt': 42,
      };

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: mixedPayload,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await usePlaygroundStore.getState().fetchRunArtifacts(mockRunId);

      expect(result?.['config.json']).toContain('"port": 8080');
      expect(result?.['count.txt']).toBe('42');
    });

    it('preserves existing selectedArtifactFile if present in newly fetched artifacts', async () => {
      const mockRunId = 'run_xyz_789';
      usePlaygroundStore.setState({
        selectedArtifactFile: 'app/page.tsx',
      });

      const mockArtifacts = {
        'package.json': '{\n  "name": "my-app"\n}',
        'app/page.tsx': 'export default function Page() { return <h1>ASEP</h1>; }',
      };

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: mockArtifacts,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      await usePlaygroundStore.getState().fetchRunArtifacts(mockRunId);

      const state = usePlaygroundStore.getState();
      expect(state.selectedArtifactFile).toBe('app/page.tsx');
    });

    it('setSelectedArtifactFile matches existing artifact even with leading slash or backslash', () => {
      usePlaygroundStore.setState({
        artifacts: {
          'src/components/Button.tsx': 'export const Button = () => null;',
        },
        selectedArtifactFile: null,
      });

      usePlaygroundStore.getState().setSelectedArtifactFile('./src/components/Button.tsx');
      expect(usePlaygroundStore.getState().selectedArtifactFile).toBe('src/components/Button.tsx');

      usePlaygroundStore.getState().setSelectedArtifactFile('src\\components\\Button.tsx');
      expect(usePlaygroundStore.getState().selectedArtifactFile).toBe('src/components/Button.tsx');
    });

    it('gracefully handles API network error when fetching artifacts', async () => {
      const mockRunId = 'run_fail_456';
      vi.spyOn(apiClient, 'get').mockRejectedValueOnce(new Error('Network error'));

      const result = await usePlaygroundStore.getState().fetchRunArtifacts(mockRunId);

      expect(result).toBeNull();
      const state = usePlaygroundStore.getState();
      expect(state.artifacts).toEqual({});
    });

    it('returns null and does not call API when runId is empty', async () => {
      const getSpy = vi.spyOn(apiClient, 'get');
      const result = await usePlaygroundStore.getState().fetchRunArtifacts('');

      expect(result).toBeNull();
      expect(getSpy).not.toHaveBeenCalled();
    });
  });
});

