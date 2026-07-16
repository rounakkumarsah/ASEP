import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { SidebarNav, DashboardSidebar } from './sidebar';
import { renderWithProviders } from '@/test/utils';

// We want to test that the navigation renders correctly, and clicking triggers callback if provided.
describe('SidebarNav and DashboardSidebar Components', () => {
  it('renders all navigation groups and links', () => {
    renderWithProviders(<SidebarNav />);
    
    // Check brand/logo
    expect(screen.getByText('ASEP')).toBeInTheDocument();
    
    // Check navigation items
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Sessions')).toBeInTheDocument();
    expect(screen.getByText('Playground')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
    expect(screen.getByText('Knowledge')).toBeInTheDocument();
    expect(screen.getByText('Governance')).toBeInTheDocument();
    expect(screen.getByText('Approvals')).toBeInTheDocument();
    expect(screen.getByText('Evaluation')).toBeInTheDocument();
    expect(screen.getByText('Metrics')).toBeInTheDocument();
    expect(screen.getByText('Audit')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('triggers onClick when a link is clicked', () => {
    const onClick = vi.fn();
    renderWithProviders(<SidebarNav onClick={onClick} />);
    
    const overviewLink = screen.getByText('Overview');
    fireEvent.click(overviewLink);
    
    expect(onClick).toHaveBeenCalled();
  });

  it('renders DashboardSidebar correctly', () => {
    renderWithProviders(<DashboardSidebar />);
    expect(screen.getByText('ASEP')).toBeInTheDocument();
  });
});
