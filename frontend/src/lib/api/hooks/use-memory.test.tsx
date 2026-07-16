import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useMemories } from './use-memory';
import { memoryService } from '../services/memory';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as React from 'react';

vi.mock('../services/memory', () => {
  return {
    memoryService: {
      getMemories: vi.fn().mockResolvedValue({
        status: 'success',
        data: {
          items: [
            {
              id: 'm1',
              type: 'working',
              content: 'Mocked working memory',
              tags: ['mock'],
              confidence: 0.9,
              createdAt: '2026-07-16T12:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          size: 50,
          pages: 1,
        },
      }),
    },
  };
});

describe('useMemories Hook', () => {
  it('fetches memories successfully via react-query', async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useMemories('working', 'query'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.items[0].content).toBe('Mocked working memory');
    expect(memoryService.getMemories).toHaveBeenCalledWith('working', 'query');
  });
});
