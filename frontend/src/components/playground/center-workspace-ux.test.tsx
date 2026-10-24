import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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
  getPhaseMetadata,
  parsePhaseFromStatusString,
  extractPhaseSummary,
  PhaseEventItem,
  PhaseStatusCard,
  formatNodeName,
  ExecutionStep,
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

    it('dynamically updates selectedArtifactFile when setArtifacts is called with files', () => {
      usePlaygroundStore.setState({ artifacts: {}, selectedArtifactFile: null });
      usePlaygroundStore.getState().setArtifacts({
        'app/page.tsx': 'export default function Page() {}',
        'package.json': '{"name": "test"}',
      });

      const state = usePlaygroundStore.getState();
      expect(Object.keys(state.artifacts)).toEqual(['app/page.tsx', 'package.json']);
      expect(state.selectedArtifactFile).toBe('app/page.tsx');
    });

    it('resets selectedArtifactFile to null when setArtifacts is called with empty object', () => {
      usePlaygroundStore.setState({
        artifacts: { 'main.py': 'print("hello")' },
        selectedArtifactFile: 'main.py',
      });
      usePlaygroundStore.getState().setArtifacts({});

      const state = usePlaygroundStore.getState();
      expect(state.artifacts).toEqual({});
      expect(state.selectedArtifactFile).toBeNull();
    });

    it('updates selectedArtifactFile to first available key when current selection is removed', () => {
      usePlaygroundStore.setState({
        artifacts: { 'file1.ts': '// 1', 'file2.ts': '// 2' },
        selectedArtifactFile: 'file2.ts',
      });
      usePlaygroundStore.getState().setArtifacts({
        'file3.ts': '// 3',
        'file4.ts': '// 4',
      });

      const state = usePlaygroundStore.getState();
      expect(state.selectedArtifactFile).toBe('file3.ts');
    });

    it('supports functional updater in setArtifacts while maintaining valid selection', () => {
      usePlaygroundStore.setState({
        artifacts: { 'a.py': 'x = 1' },
        selectedArtifactFile: 'a.py',
      });
      usePlaygroundStore.getState().setArtifacts((prev) => ({
        ...prev,
        'b.py': 'y = 2',
      }));

      const state = usePlaygroundStore.getState();
      expect(Object.keys(state.artifacts)).toEqual(['a.py', 'b.py']);
      expect(state.selectedArtifactFile).toBe('a.py');
    });

    it('normalizes paths with backslashes and leading dot-slashes in setArtifacts', () => {
      usePlaygroundStore.setState({ artifacts: {}, selectedArtifactFile: null });
      usePlaygroundStore.getState().setArtifacts({
        'src\\components\\App.tsx': 'export const App = () => null;',
        './package.json': '{"name": "test"}',
        '/index.html': '<html />',
      });

      const state = usePlaygroundStore.getState();
      expect(Object.keys(state.artifacts)).toEqual([
        'src/components/App.tsx',
        'package.json',
        'index.html',
      ]);
      expect(state.selectedArtifactFile).toBe('src/components/App.tsx');
    });

    it('returns null and does not corrupt store when fetchRunArtifacts receives error/detail payload', async () => {
      usePlaygroundStore.setState({
        artifacts: { 'existing.py': 'print(1)' },
        selectedArtifactFile: 'existing.py',
      });
      vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: { detail: 'Run 1234 not found' },
      });

      const result = await usePlaygroundStore.getState().fetchRunArtifacts('1234');
      expect(result).toBeNull();
      const state = usePlaygroundStore.getState();
      expect(state.artifacts).toEqual({ 'existing.py': 'print(1)' });
      expect(state.selectedArtifactFile).toBe('existing.py');
    });

    it('unwraps nested artifacts object and normalizes keys in fetchRunArtifacts', async () => {
      usePlaygroundStore.setState({ artifacts: {}, selectedArtifactFile: null });
      vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: {
          run_id: 'run-abc',
          artifacts: {
            'lib\\utils.ts': 'export const sum = (a, b) => a + b;',
            './README.md': '# Hello',
          },
        },
      });

      const result = await usePlaygroundStore.getState().fetchRunArtifacts('run-abc');
      expect(result).toEqual({
        'lib/utils.ts': 'export const sum = (a, b) => a + b;',
        'README.md': '# Hello',
      });

      const state = usePlaygroundStore.getState();
      expect(Object.keys(state.artifacts)).toEqual(['lib/utils.ts', 'README.md']);
      expect(state.selectedArtifactFile).toBe('lib/utils.ts');
    });

    it('normalizes path when setSelectedArtifactFile is called with backslashes or leading dot-slash', () => {
      usePlaygroundStore.setState({
        artifacts: {
          'src/index.ts': '// code',
          'docs/readme.md': '# doc',
        },
        selectedArtifactFile: 'src/index.ts',
      });

      usePlaygroundStore.getState().setSelectedArtifactFile('.\\docs\\readme.md');
      expect(usePlaygroundStore.getState().selectedArtifactFile).toBe('docs/readme.md');

      usePlaygroundStore.getState().setSelectedArtifactFile(null);
      expect(usePlaygroundStore.getState().selectedArtifactFile).toBeNull();
    });
  });

  describe('Phase Event Streaming & Parsing (Chat UI Live Progress)', () => {
    describe('getPhaseMetadata()', () => {
      it('resolves pipeline nodes to dynamic title-cased names', () => {
        expect(getPhaseMetadata('research')?.name).toBe('Research');
        expect(getPhaseMetadata('implement')?.name).toBe('Implement');
        expect(getPhaseMetadata('test')?.name).toBe('Test');
        expect(getPhaseMetadata('critic')?.name).toBe('Critic');
        expect(getPhaseMetadata('security_audit')?.name).toBe('Security Audit');
        expect(getPhaseMetadata('deploy')?.name).toBe('Deploy');
      });

      it('resolves lifecycle nodes dynamically without hardcoding', () => {
        expect(getPhaseMetadata('start')?.name).toBe('Start');
        expect(getPhaseMetadata('orchestrator')?.name).toBe('Orchestrator');
        expect(getPhaseMetadata('end')?.name).toBe('End');
        expect(getPhaseMetadata('')).toBeNull();
      });
    });

    describe('parsePhaseFromStatusString()', () => {
      it('parses Implement Phase Complete string and extracts summary', () => {
        const parsed = parsePhaseFromStatusString('Implement Phase Complete: Core modules coded.');
        expect(parsed).toEqual({
          phase: 'implement',
          phaseName: 'Implement',
          status: 'completed',
          summary: 'Core modules coded',
          icon: '⚙️',
        });
      });

      it('parses Test Phase Complete string and extracts summary', () => {
        const parsed = parsePhaseFromStatusString('Test Phase Complete: All units passed.');
        expect(parsed).toEqual({
          phase: 'test',
          phaseName: 'Test',
          status: 'completed',
          summary: 'All units passed',
          icon: '⚙️',
        });
      });

      it('parses Critic Phase Complete string dynamically', () => {
        const parsed = parsePhaseFromStatusString('Critic Phase Complete: Sandbox execution verified successfully');
        expect(parsed).toEqual({
          phase: 'critic',
          phaseName: 'Critic',
          status: 'completed',
          summary: 'Sandbox execution verified successfully',
          icon: '⚙️',
        });
      });

      it('parses Security Audit Complete string and extracts summary', () => {
        const parsed = parsePhaseFromStatusString('Security Audit Complete: Verified with 0 critical vulnerabilities (0 High, 0 Medium, 0 Low).');
        expect(parsed?.phase).toBe('security_audit');
        expect(parsed?.phaseName).toBe('Security Audit');
        expect(parsed?.status).toBe('completed');
        expect(parsed?.icon).toBe('⚙️');
      });

      it('parses Deploy Phase Complete string and extracts summary', () => {
        const parsed = parsePhaseFromStatusString('Deploy Phase Complete: Artifacts bundled and verified against security policies.');
        expect(parsed).toEqual({
          phase: 'deploy',
          phaseName: 'Deploy',
          status: 'completed',
          summary: 'Artifacts bundled and verified against security policies',
          icon: '⚙️',
        });
      });

      it('parses Phase started strings and marks active status', () => {
        const parsed = parsePhaseFromStatusString('Phase started: implement');
        expect(parsed).toEqual({
          phase: 'implement',
          phaseName: 'Implement',
          status: 'active',
          summary: 'Running implement...',
          icon: '⚙️',
        });
      });
    });

    describe('extractPhaseSummary()', () => {
      it('extracts summary from messages containing phase completion strings', () => {
        const updateVal = {
          messages: [
            { role: 'system', content: 'Implement Phase Complete: Core modules coded.' },
          ],
        };
        expect(extractPhaseSummary(updateVal, 'implement')).toBe('Core modules coded');
      });

      it('extracts summary from security_report object', () => {
        const updateVal = {
          security_report: { critical_count: 0, high_count: 0 },
        };
        expect(extractPhaseSummary(updateVal, 'security_audit')).toBe('0 vulnerabilities');
      });

      it('extracts summary from test_results object', () => {
        const updateVal = {
          test_results: { status: 'PASS', coverage: '95%' },
        };
        expect(extractPhaseSummary(updateVal, 'test')).toBe('All tests passed (95%)');
      });

      it('falls back to default summary when update object has no custom summary', () => {
        expect(extractPhaseSummary({}, 'deploy')).toBe('Deploy executed');
      });
    });

    describe('processEventData() with onPhaseEvent handler', () => {
      it('triggers onPhaseEvent for all intermediate phases in sequential order', () => {
        const capturedPhaseEvents: PhaseEventItem[] = [];
        const onPhaseEvent = vi.fn((event: PhaseEventItem) => {
          capturedPhaseEvents.push(event);
        });

        // Step 1: Research
        processEventData(
          {
            event: {
              research: {
                messages: [{ role: 'system', content: 'Research Phase Complete: Loaded documentation.' }],
              },
            },
          },
          { onPhaseEvent }
        );

        // Step 2: Implement
        processEventData(
          {
            event: {
              implement: {
                messages: [{ role: 'system', content: 'Implement Phase Complete: Core modules coded.' }],
                generated_code: 'export const app = () => {};',
              },
            },
          },
          { onPhaseEvent }
        );

        // Step 3: Test
        processEventData(
          {
            event: {
              test: {
                messages: [{ role: 'system', content: 'Test Phase Complete: All units passed.' }],
              },
            },
          },
          { onPhaseEvent }
        );

        // Step 4: Security Audit
        processEventData(
          {
            event: {
              security_audit: {
                messages: [{ role: 'system', content: 'Security Audit Complete: Verified with 0 critical vulnerabilities.' }],
              },
            },
          },
          { onPhaseEvent }
        );

        // Step 5: Deploy
        processEventData(
          {
            event: {
              deploy: {
                messages: [{ role: 'system', content: 'Deploy Phase Complete: Completed.' }],
              },
            },
          },
          { onPhaseEvent }
        );

        expect(capturedPhaseEvents).toHaveLength(5);
        expect(capturedPhaseEvents.map((p) => p.phase)).toEqual([
          'research',
          'implement',
          'test',
          'security_audit',
          'deploy',
        ]);
        expect(capturedPhaseEvents.map((p) => p.status)).toEqual([
          'completed',
          'completed',
          'completed',
          'completed',
          'completed',
        ]);
        expect(capturedPhaseEvents[1].summary).toBe('Core modules coded');
        expect(capturedPhaseEvents[2].summary).toBe('All units passed');
      });
    });
  });

  describe('Dynamic LangGraph Node Execution Steps & Store Integration', () => {
    describe('formatNodeName()', () => {
      it('converts snake_case names into Title Case', () => {
        expect(formatNodeName('agent_loop_implementation')).toBe('Agent Loop Implementation');
        expect(formatNodeName('memory_state_design')).toBe('Memory State Design');
        expect(formatNodeName('sandbox_tests')).toBe('Sandbox Tests');
        expect(formatNodeName('capability_blueprint_design')).toBe('Capability Blueprint Design');
      });

      it('converts kebab-case names into Title Case', () => {
        expect(formatNodeName('code-review-critic')).toBe('Code Review Critic');
        expect(formatNodeName('ast-slicer')).toBe('Ast Slicer');
      });

      it('preserves already Title Cased names', () => {
        expect(formatNodeName('Agent Loop Implementation')).toBe('Agent Loop Implementation');
        expect(formatNodeName('Orchestrator')).toBe('Orchestrator');
      });

      it('handles empty or blank input gracefully', () => {
        expect(formatNodeName('')).toBe('');
        expect(formatNodeName('   ')).toBe('');
      });
    });

    describe('processEventData() dynamic node execution steps', () => {
      it('processes direct node_name events and triggers onExecutionStep', () => {
        const capturedSteps: ExecutionStep[] = [];
        processEventData(
          {
            event: {
              node_name: 'agent_loop_implementation',
              status: 'running',
              summary: 'Implementing core loop logic',
            },
          },
          {
            onExecutionStep: (step) => capturedSteps.push(step),
          }
        );

        expect(capturedSteps).toHaveLength(1);
        expect(capturedSteps[0]).toEqual({
          id: 'agent_loop_implementation',
          nodeName: 'Agent Loop Implementation',
          status: 'running',
          summary: 'Implementing core loop logic',
        });
      });

      it('processes dynamic node dictionary updates without hardcoded keys', () => {
        const capturedSteps: ExecutionStep[] = [];
        processEventData(
          {
            event: {
              custom_dynamic_node_42: {
                status: 'completed',
                summary: 'Completed dynamic custom step 42',
              },
            },
          },
          {
            onExecutionStep: (step) => capturedSteps.push(step),
          }
        );

        expect(capturedSteps).toHaveLength(1);
        expect(capturedSteps[0]).toEqual({
          id: 'custom_dynamic_node_42',
          nodeName: 'Custom Dynamic Node 42',
          status: 'completed',
          summary: 'Completed dynamic custom step 42',
        });
      });

      it('handles failed step status correctly', () => {
        const capturedSteps: ExecutionStep[] = [];
        processEventData(
          {
            event: {
              sandbox_evaluation: {
                status: 'failed',
                message: 'SyntaxError in test runner',
              },
            },
          },
          {
            onExecutionStep: (step) => capturedSteps.push(step),
          }
        );

        expect(capturedSteps).toHaveLength(1);
        expect(capturedSteps[0].status).toBe('failed');
        expect(capturedSteps[0].nodeName).toBe('Sandbox Evaluation');
      });

      it('ignores metadata keys like status, run_id, messages, nodes_executed and does not create steps for them', () => {
        const capturedSteps: ExecutionStep[] = [];
        processEventData(
          {
            event: {
              status: 'running',
              run_id: 'test-run-123',
              thread_id: 'test-thread-456',
              messages: [{ role: 'system', content: 'test message' }],
              nodes_executed: ['research'],
            },
          },
          {
            onExecutionStep: (step) => capturedSteps.push(step),
          }
        );

        expect(capturedSteps).toHaveLength(0);
      });

      it('processes any of the 25 LangGraph nodes dynamically', () => {
        const capturedSteps: ExecutionStep[] = [];
        const nodes25 = [
          'start', 'orchestrator', 'planner', 'research', 'blueprint',
          'capability_blueprint_design', 'scaffold', 'memory_state_design',
          'agent_loop_implementation', 'tool_calling_system', 'self_healing_debugger',
          'sandbox_evaluation', 'critic', 'code_review_critic', 'security_audit',
          'test_generator', 'sandbox_tests', 'ast_slicer', 'diff_patcher',
          'doc_crawler', 'package_resolver', 'human_in_the_loop', 'deploy',
          'observability_telemetry', 'end'
        ];

        for (const node of nodes25) {
          processEventData(
            {
              event: {
                [node]: {
                  status: 'running',
                  summary: `Executing node ${node}`,
                },
              },
            },
            {
              onExecutionStep: (step) => capturedSteps.push(step),
            }
          );
        }

        expect(capturedSteps).toHaveLength(25);
        expect(capturedSteps[4].nodeName).toBe('Blueprint');
        expect(capturedSteps[7].nodeName).toBe('Memory State Design');
        expect(capturedSteps[8].nodeName).toBe('Agent Loop Implementation');
      });
    });

    describe('playgroundStore executionSteps transitions', () => {
      beforeEach(() => {
        usePlaygroundStore.getState().clearExecutionSteps();
      });

      it('normalizes keys with spaces and underscores correctly without character stripping bugs', () => {
        usePlaygroundStore.getState().addExecutionStep({
          id: 'sandbox_tests',
          nodeName: 'Sandbox Tests',
          status: 'running',
        });

        // Update with Title Case name containing spaces and 's' characters
        usePlaygroundStore.getState().updateExecutionStep('Sandbox Tests', {
          status: 'completed',
          summary: 'All sandbox tests passed',
        });

        const steps = usePlaygroundStore.getState().executionSteps;
        expect(steps).toHaveLength(1);
        expect(steps[0].status).toBe('completed');
        expect(steps[0].summary).toBe('All sandbox tests passed');
      });

      it('automatically completes previously running steps when a new step starts running', () => {
        usePlaygroundStore.getState().addExecutionStep({
          id: 'research',
          nodeName: 'Research',
          status: 'running',
        });
        expect(usePlaygroundStore.getState().executionSteps[0].status).toBe('running');

        // Next step begins
        usePlaygroundStore.getState().addExecutionStep({
          id: 'blueprint',
          nodeName: 'Blueprint',
          status: 'running',
        });

        const steps = usePlaygroundStore.getState().executionSteps;
        expect(steps).toHaveLength(2);
        expect(steps[0].id).toBe('research');
        expect(steps[0].status).toBe('completed');
        expect(steps[1].id).toBe('blueprint');
        expect(steps[1].status).toBe('running');
      });

      it('creates step via updateExecutionStep if it does not yet exist', () => {
        usePlaygroundStore.getState().updateExecutionStep('agent_loop_implementation', {
          status: 'running',
          summary: 'Implementing loop',
        });

        const steps = usePlaygroundStore.getState().executionSteps;
        expect(steps).toHaveLength(1);
        expect(steps[0].id).toBe('agent_loop_implementation');
        expect(steps[0].nodeName).toBe('Agent Loop Implementation');
        expect(steps[0].status).toBe('running');
      });

      it('clears execution steps when resetActiveNodes is called', () => {
        usePlaygroundStore.getState().addExecutionStep({
          id: 'research',
          nodeName: 'Research',
          status: 'completed',
        });
        expect(usePlaygroundStore.getState().executionSteps).toHaveLength(1);

        usePlaygroundStore.getState().resetActiveNodes();
        expect(usePlaygroundStore.getState().executionSteps).toHaveLength(0);
      });
    });
  });

  describe('PhaseStatusCard Component Rendering & Interaction', () => {
    it('renders active phase with spinner and active badge', () => {
      const phaseData: PhaseEventItem = {
        phase: 'implement',
        phaseName: 'Implementation Phase',
        status: 'active',
        summary: 'Generating core modules...',
        icon: '⚙️',
      };

      render(<PhaseStatusCard phaseData={phaseData} />);

      expect(screen.getByTestId('phase-status-card-implement')).toBeDefined();
      expect(screen.getByText('Implementation Phase')).toBeDefined();
      expect(screen.getByText('Generating core modules...')).toBeDefined();
      expect(screen.getByTestId('phase-badge-implement').textContent).toContain('Active');
    });

    it('renders completed phase with done checkmark badge', () => {
      const phaseData: PhaseEventItem = {
        phase: 'test',
        phaseName: 'Test Phase',
        status: 'completed',
        summary: 'All tests passed',
        icon: '🧪',
      };

      render(<PhaseStatusCard phaseData={phaseData} />);

      expect(screen.getByTestId('phase-status-card-test')).toBeDefined();
      expect(screen.getByText('Test Phase')).toBeDefined();
      expect(screen.getByText('All tests passed')).toBeDefined();
      expect(screen.getByTestId('phase-badge-test').textContent).toContain('Done');
    });

    it('renders failed phase with failed badge', () => {
      const phaseData: PhaseEventItem = {
        phase: 'security_audit',
        phaseName: 'Security Audit Phase',
        status: 'failed',
        summary: '2 critical vulnerabilities found',
        icon: '🛡️',
      };

      render(<PhaseStatusCard phaseData={phaseData} />);

      expect(screen.getByTestId('phase-status-card-security_audit')).toBeDefined();
      expect(screen.getByTestId('phase-badge-security_audit').textContent).toContain('Failed');
    });

    it('toggles collapsible accordion and displays detailed summary and artifacts button', () => {
      const onViewArtifacts = vi.fn();
      const phaseData: PhaseEventItem = {
        phase: 'implement',
        phaseName: 'Implementation Phase',
        status: 'completed',
        summary: '5 modules coded successfully',
        icon: '⚙️',
      };

      render(<PhaseStatusCard phaseData={phaseData} onViewArtifacts={onViewArtifacts} />);

      // Initially collapsed, "View Code Artifacts" should not be visible
      expect(screen.queryByText('View Code Artifacts')).toBeNull();

      // Click header bar to expand
      const headerBar = screen.getByText('Implementation Phase');
      fireEvent.click(headerBar);

      // Now expanded
      const viewBtn = screen.getByText('View Code Artifacts');
      expect(viewBtn).toBeDefined();

      fireEvent.click(viewBtn);
      expect(onViewArtifacts).toHaveBeenCalledTimes(1);

      // Click again to collapse
      fireEvent.click(headerBar);
      expect(screen.queryByText('View Code Artifacts')).toBeNull();
    });
  });

  describe('getPhaseMetadata() dynamic handling', () => {
    it('formats node keys dynamically to title case', () => {
      expect(getPhaseMetadata('exploration')?.key).toBe('exploration');
      expect(getPhaseMetadata('exploration')?.name).toBe('Exploration');
      expect(getPhaseMetadata('agent_loop_implementation')?.name).toBe('Agent Loop Implementation');
      expect(getPhaseMetadata('planner_executor_critic_architecture')?.name).toBe('Planner Executor Critic Architecture');
      expect(getPhaseMetadata('start')?.name).toBe('Start');
      expect(getPhaseMetadata('orchestrator')?.name).toBe('Orchestrator');
      expect(getPhaseMetadata('end')?.name).toBe('End');
    });

    it('returns null for empty strings or invalid input', () => {
      expect(getPhaseMetadata('')).toBeNull();
      expect(getPhaseMetadata('   ')).toBeNull();
    });
  });

  describe('parsePhaseFromStatusString() generic completion support', () => {
    it('parses generic Phase complete: <phase>: <summary> format', () => {
      const res = parsePhaseFromStatusString('Phase complete: implement: 4 modules compiled.');
      expect(res).toEqual({
        phase: 'implement',
        phaseName: 'Implement',
        status: 'completed',
        summary: '4 modules compiled',
        icon: '⚙️',
      });
    });

    it('parses generic Phase completed: <phase> format with default summary', () => {
      const res = parsePhaseFromStatusString('Phase completed: deploy');
      expect(res).toEqual({
        phase: 'deploy',
        phaseName: 'Deploy',
        status: 'completed',
        summary: 'Deploy executed',
        icon: '⚙️',
      });
    });

    it('parses dynamic snake_case LangGraph node completion strings', () => {
      const res = parsePhaseFromStatusString('Agent Loop Implementation Complete: Cyclic loop constructed with 4 tools.');
      expect(res).toEqual({
        phase: 'agent_loop_implementation',
        phaseName: 'Agent Loop Implementation',
        status: 'completed',
        summary: 'Cyclic loop constructed with 4 tools',
        icon: '⚙️',
      });
    });

    it('parses dynamic node with Phase keyword', () => {
      const res = parsePhaseFromStatusString('Planner Executor Critic Architecture Phase Complete: Architecture validated.');
      expect(res).toEqual({
        phase: 'planner_executor_critic_architecture',
        phaseName: 'Planner Executor Critic Architecture',
        status: 'completed',
        summary: 'Architecture validated',
        icon: '⚙️',
      });
    });
  });

  describe('Strict 32 Backend LangGraph Nodes Formatting and Skipped Nodes Handling', () => {
    const ALL_32_BACKEND_NODES = [
      'start',
      'explore',
      'orchestrator',
      'research',
      'clarification_gate',
      'deploy_clarification_gate',
      'blueprint',
      'scaffold',
      'implement',
      'critic',
      'debugger',
      'test',
      'security_audit',
      'deploy',
      'host_manager',
      'capability_blueprint',
      'tool_design',
      'agent_loop_implementation',
      'memory_state_design',
      'sandbox_tests',
      'evaluation_runs',
      'goal_decomposition_design',
      'planner_executor_critic_architecture',
      'tool_integration',
      'multi_step_test_scenarios',
      'failure_recovery_tests',
      'workflow_mapping',
      'trigger_action_design',
      'integration_points',
      'end_to_end_automation_tests',
      'error_handling_paths',
      'end',
    ];

    it('correctly converts all 32 real backend LangGraph nodes to Title Case', () => {
      const formatted = ALL_32_BACKEND_NODES.map(formatNodeName);
      expect(formatted).toEqual([
        'Start',
        'Explore',
        'Orchestrator',
        'Research',
        'Clarification Gate',
        'Deploy Clarification Gate',
        'Blueprint',
        'Scaffold',
        'Implement',
        'Critic',
        'Debugger',
        'Test',
        'Security Audit',
        'Deploy',
        'Host Manager',
        'Capability Blueprint',
        'Tool Design',
        'Agent Loop Implementation',
        'Memory State Design',
        'Sandbox Tests',
        'Evaluation Runs',
        'Goal Decomposition Design',
        'Planner Executor Critic Architecture',
        'Tool Integration',
        'Multi Step Test Scenarios',
        'Failure Recovery Tests',
        'Workflow Mapping',
        'Trigger Action Design',
        'Integration Points',
        'End To End Automation Tests',
        'Error Handling Paths',
        'End',
      ]);
    });

    it('gracefully handles skipped nodes without creating phantom or fallback steps', () => {
      usePlaygroundStore.getState().clearExecutionSteps();

      // Backend skips clarification_gate, critic, debugger, security_audit, etc.
      // Emits only 3 nodes in this run:
      const emittedEvents = [
        { research: { status: 'completed', summary: 'Gathered context' } },
        { implement: { status: 'completed', summary: 'Generated core code' } },
        { deploy: { status: 'completed', summary: 'Deployed to staging' } },
      ];

      for (const ev of emittedEvents) {
        processEventData(
          { event: ev },
          {
            onExecutionStep: (step) => {
              usePlaygroundStore.getState().addExecutionStep(step);
            },
          }
        );
      }

      const steps = usePlaygroundStore.getState().executionSteps;
      expect(steps).toHaveLength(3);
      expect(steps.map((s) => s.id)).toEqual(['research', 'implement', 'deploy']);
      expect(steps.map((s) => s.nodeName)).toEqual(['Research', 'Implement', 'Deploy']);

      // Verify that skipped nodes are NOT present in executionSteps
      const skippedNodes = ['clarification_gate', 'critic', 'debugger', 'security_audit', 'sandbox_tests'];
      for (const skipped of skippedNodes) {
        expect(steps.some((s) => s.id === skipped)).toBe(false);
      }
    });

    it('updateExecutionStep always formats nodeName to Title Case even when passed snake_case', () => {
      usePlaygroundStore.getState().clearExecutionSteps();

      // Step does not exist yet; create via updateExecutionStep
      usePlaygroundStore.getState().updateExecutionStep('agent_loop_implementation', {
        nodeName: 'agent_loop_implementation',
        status: 'running',
        summary: 'Building cyclic graph',
      });

      const steps = usePlaygroundStore.getState().executionSteps;
      expect(steps).toHaveLength(1);
      expect(steps[0].nodeName).toBe('Agent Loop Implementation');
      expect(steps[0].status).toBe('running');

      // Update existing step with another snake_case nodeName
      usePlaygroundStore.getState().updateExecutionStep('agent_loop_implementation', {
        nodeName: 'agent_loop_implementation_updated',
        status: 'completed',
      });

      const updatedSteps = usePlaygroundStore.getState().executionSteps;
      expect(updatedSteps).toHaveLength(1);
      expect(updatedSteps[0].nodeName).toBe('Agent Loop Implementation Updated');
      expect(updatedSteps[0].status).toBe('completed');
    });
  });
});


