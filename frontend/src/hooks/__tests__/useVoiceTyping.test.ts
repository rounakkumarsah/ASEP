import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVoiceTyping } from '../useVoiceTyping';
import { usePlaygroundStore } from '@/lib/stores/playgroundStore';

describe('useVoiceTyping Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePlaygroundStore.setState({
      voiceMetrics: {
        totalTranscriptions: 0,
        providerUsage: { groq: 0, gemini: 0, openrouter: 0, webSpeech: 0 },
        lastLatencyMs: {},
        failoverEvents: [],
      },
    });
  });

  it('initializes with isListening=false and isTranscribing=false', () => {
    const onTranscript = vi.fn();
    const onToast = vi.fn();

    const { result } = renderHook(() =>
      useVoiceTyping({ onTranscript, onToast })
    );

    expect(result.current.isListening).toBe(false);
    expect(result.current.isTranscribing).toBe(false);
    expect(typeof result.current.toggleListening).toBe('function');
  });

  it('records voice metrics when recordVoiceTranscription is invoked', () => {
    const record = usePlaygroundStore.getState().recordVoiceTranscription;

    act(() => {
      record('groq', 350.5, []);
    });

    const metrics = usePlaygroundStore.getState().voiceMetrics;
    expect(metrics.totalTranscriptions).toBe(1);
    expect(metrics.providerUsage.groq).toBe(1);
    expect(metrics.lastLatencyMs.groq).toBe(350.5);
    expect(metrics.failoverEvents).toHaveLength(0);
  });

  it('records failover event and updates backup provider metrics', () => {
    const record = usePlaygroundStore.getState().recordVoiceTranscription;

    act(() => {
      record('gemini', 520.0, [
        {
          from: 'groq',
          to: 'gemini',
          reason: '429 Rate limit',
          toast: 'Groq busy → switching to Gemini',
        },
      ]);
    });

    const metrics = usePlaygroundStore.getState().voiceMetrics;
    expect(metrics.totalTranscriptions).toBe(1);
    expect(metrics.providerUsage.gemini).toBe(1);
    expect(metrics.lastLatencyMs.gemini).toBe(520.0);
    expect(metrics.failoverEvents).toHaveLength(1);
    expect(metrics.failoverEvents[0].from).toBe('groq');
    expect(metrics.failoverEvents[0].to).toBe('gemini');
    expect(metrics.failoverEvents[0].toast).toBe('Groq busy → switching to Gemini');
  });

  it('records OpenRouter fallback after Groq and Gemini fail', () => {
    const record = usePlaygroundStore.getState().recordVoiceTranscription;

    act(() => {
      record('openrouter', 810.0, [
        { from: 'groq', to: 'gemini', reason: '429', toast: 'Groq busy → switching to Gemini' },
        { from: 'gemini', to: 'openrouter', reason: '500', toast: 'Gemini busy → switching to OpenRouter' },
      ]);
    });

    const metrics = usePlaygroundStore.getState().voiceMetrics;
    expect(metrics.totalTranscriptions).toBe(1);
    expect(metrics.providerUsage.openrouter).toBe(1);
    expect(metrics.lastLatencyMs.openrouter).toBe(810.0);
    expect(metrics.failoverEvents).toHaveLength(2);
  });
});
