import { describe, it, expect, vi } from 'vitest';
import {
  classifyEvent,
  extractMessageContent,
  isStatusContent,
  processEventData,
  MessageItem,
} from './CenterWorkspace';

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
});
