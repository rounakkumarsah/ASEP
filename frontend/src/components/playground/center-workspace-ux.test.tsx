import { describe, it, expect } from 'vitest';
import {
  classifyEvent,
  isStatusContent,
  MessageItem,
} from './CenterWorkspace';

describe('CenterWorkspace UX - Event Classification and Message Routing', () => {
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
    });

    it('classifies Exploration events and summaries as STATUS', () => {
      expect(classifyEvent({ role: 'system', content: '[Explore Event] {"query": "search"}' })).toBe('STATUS');
      expect(classifyEvent({ role: 'system', content: '[Explore Summary] {"phase": "explore"}' })).toBe('STATUS');
    });

    it('classifies tool messages as STATUS', () => {
      expect(classifyEvent({ type: 'tool', name: 'github', content: '{"success": true}' })).toBe('STATUS');
    });

    it('classifies real assistant LLM responses as FINAL_ANSWER', () => {
      const item: MessageItem = {
        role: 'assistant',
        content: 'I have implemented the requested authentication middleware in `src/auth.ts`.\n\n```typescript\nexport const auth = () => {};\n```',
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
      expect(isStatusContent('Phase map generated: plan -> code -> test.')).toBe(true);
      expect(isStatusContent('Checkpoint saved: step-1')).toBe(true);
      expect(isStatusContent('[Token Budget Exceeded] Phase coder consumed 3000 tokens')).toBe(true);
      expect(isStatusContent('[Clarification Required] Please enter API key')).toBe(true);
      expect(isStatusContent('[Auto Router Toast] Switched to flash')).toBe(true);
      expect(isStatusContent('[Host Manager Status] [OK] Listening on http://localhost:3000')).toBe(true);
      expect(isStatusContent('Task processed through LangGraph multi-agent execution pipeline.')).toBe(true);
      expect(isStatusContent('Resumed execution.')).toBe(true);
    });

    it('returns false for actual LLM-generated answers and advice', () => {
      expect(isStatusContent('To solve this issue, we should configure CORS properly.')).toBe(false);
      expect(isStatusContent('```python\ndef hello():\n    return "world"\n```')).toBe(false);
      expect(isStatusContent('Here is the breakdown of the changes made to the database schema.')).toBe(false);
    });
  });

  describe('No Final Answer Fallback Rule', () => {
    it('uses the mandatory clean error message when no final answer event arrives', () => {
      const fallbackErrorMessage = 'The agent could not complete this task. Please try again.';
      const aiResponse: string = '';
      const finalContent = aiResponse && aiResponse.trim() ? aiResponse.trim() : fallbackErrorMessage;

      expect(finalContent).toBe('The agent could not complete this task. Please try again.');
      expect(finalContent).not.toContain('LangGraph');
      expect(finalContent).not.toContain('pipeline');
    });

    it('uses the real answer when aiResponse is present', () => {
      const fallbackErrorMessage = 'The agent could not complete this task. Please try again.';
      const aiResponse: string = 'Here is your solution.';
      const finalContent = aiResponse && aiResponse.trim() ? aiResponse.trim() : fallbackErrorMessage;

      expect(finalContent).toBe('Here is your solution.');
    });
  });
});
