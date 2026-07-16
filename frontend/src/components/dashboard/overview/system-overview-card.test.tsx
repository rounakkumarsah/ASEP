import * as React from 'react';
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { SystemOverviewCard } from './system-overview-card';
import { renderWithProviders } from '@/test/utils';
import { SystemHealth } from '@/lib/api/types';

describe('SystemOverviewCard Component', () => {
  const mockHealth: SystemHealth = {
    status: 'operational',
    uptime: 172800, // 2 days in seconds
    cpuUsage: 45,
    memoryUsage: 60,
    activeAgents: 3,
    activeSessions: 5,
    pendingApprovals: 2,
    lastUpdated: '2026-07-16T12:00:00Z',
  };

  it('renders uptime, cpu usage, and memory usage correctly', () => {
    renderWithProviders(<SystemOverviewCard health={mockHealth} />);
    
    // Check main title
    expect(screen.getByText('System Overview')).toBeInTheDocument();
    
    // Check uptime days
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('days')).toBeInTheDocument();
    
    // Check cpu load text
    expect(screen.getByText('45%')).toBeInTheDocument();
    
    // Check memory text
    expect(screen.getByText('60%')).toBeInTheDocument();
  });
});
