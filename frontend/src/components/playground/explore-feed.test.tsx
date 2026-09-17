import * as React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@/test/utils';
import { ExplorationCard } from './ExplorationCard';
import { ExplorePanel } from './ExplorePanel';
import { usePlaygroundStore, ExploreEvent, ExplorationSummary } from '@/lib/stores/playgroundStore';

describe('Explore Feed Components', () => {
  beforeEach(() => {
    usePlaygroundStore.setState({
      explorationEvents: [],
      phaseExplorations: {},
      activeRightTab: 'trace',
    });
  });

  describe('ExplorationCard', () => {
    const mockSummary: ExplorationSummary = {
      phase: 'implement',
      relevant_files: ['backend/src/auth/service.py', 'backend/src/auth/router.py'],
      architecture_understanding: 'Centralized JWT auth service with Bearer token validation.',
      risks_identified: ['Token expiration not enforced in legacy routes'],
      files_explored_count: 2,
      searches_count: 3,
      duration_ms: 1250,
      tokens_saved: 3200,
    };

    it('renders header with phase, file count, and spared tokens', () => {
      renderWithProviders(<ExplorationCard summary={mockSummary} />);

      expect(screen.getByText('Exploration Phase:')).toBeInTheDocument();
      expect(screen.getByText('implement')).toBeInTheDocument();
      expect(screen.getByText('2 files explored')).toBeInTheDocument();
      expect(screen.getByText('3 searches')).toBeInTheDocument();
      expect(screen.getByText('~3.2k tokens spared')).toBeInTheDocument();
    });

    it('expands to reveal architecture understanding and risks on click', () => {
      renderWithProviders(<ExplorationCard summary={mockSummary} />);

      // Initially collapsed
      expect(screen.queryByText(/Centralized JWT auth service/)).not.toBeInTheDocument();

      // Click header to expand
      fireEvent.click(screen.getByText('Exploration Phase:'));

      // Now visible
      expect(screen.getByText('Architecture Understanding')).toBeInTheDocument();
      expect(screen.getByText(/Centralized JWT auth service/)).toBeInTheDocument();
      expect(screen.getByText('Risks Identified (1)')).toBeInTheDocument();
      expect(screen.getByText('Token expiration not enforced in legacy routes')).toBeInTheDocument();
      expect(screen.getByText('backend/src/auth/service.py')).toBeInTheDocument();
      expect(screen.getByText('Open Live Explore Feed')).toBeInTheDocument();
    });

    it('switches right tab to explore and opens panel on action button click', () => {
      renderWithProviders(<ExplorationCard summary={mockSummary} />);
      fireEvent.click(screen.getByText('Exploration Phase:'));

      const openButton = screen.getByText('Open Live Explore Feed');
      fireEvent.click(openButton);

      expect(usePlaygroundStore.getState().activeRightTab).toBe('explore');
    });
  });

  describe('ExplorePanel', () => {
    it('renders empty feed placeholder when no exploration events exist', () => {
      renderWithProviders(<ExplorePanel />);

      expect(screen.getByText('Live Exploration Feed')).toBeInTheDocument();
      expect(screen.getByText('Awaiting exploration actions...')).toBeInTheDocument();
    });

    it('renders structured events with filters and duration', () => {
      const mockEvents: ExploreEvent[] = [
        {
          id: 'ev-1',
          phase: 'research',
          type: 'search',
          detail: 'Searching workspace for pattern "*auth*"',
          duration_ms: 120,
          timestamp: '12:00',
          match_count: 5,
          status: 'completed',
        },
        {
          id: 'ev-2',
          phase: 'research',
          type: 'read',
          detail: 'Reading file src/auth/service.py (first 20 lines)',
          file: 'src/auth/service.py',
          duration_ms: 45,
          timestamp: '12:01',
          size_bytes: 2048,
          content_preview: 'import jwt\ndef get_token(): pass',
          status: 'completed',
        },
        {
          id: 'ev-3',
          phase: 'research',
          type: 'think',
          detail: 'Analyzing auth architecture and session handling',
          duration_ms: 4100,
          timestamp: '12:02',
          status: 'completed',
        },
      ];

      usePlaygroundStore.setState({ explorationEvents: mockEvents });

      renderWithProviders(<ExplorePanel />);

      expect(screen.getByText('Live Exploration Feed')).toBeInTheDocument();
      expect(screen.getByText('3 events')).toBeInTheDocument();

      // Search event
      expect(screen.getByText('Searching workspace for pattern "*auth*"')).toBeInTheDocument();
      expect(screen.getByText('5 matches')).toBeInTheDocument();

      // Read event
      expect(screen.getByText(/Reading file src\/auth\/service\.py/)).toBeInTheDocument();

      // Thought event
      expect(screen.getByText('Analyzing auth architecture and session handling')).toBeInTheDocument();
      expect(screen.getByText('(4.1s)')).toBeInTheDocument();
    });
  });
});
