import * as React from 'react';
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { ApprovalCard } from './approval-card';
import { renderWithProviders } from '@/test/utils';
import { ApprovalRequest } from '@/lib/api/types';

describe('ApprovalCard Component', () => {
  const mockApproval: ApprovalRequest = {
    id: 'a1',
    agentId: 'coder-agent',
    requestedAction: 'Deploy package to production',
    justification: 'Critical fix for payment gateway authentication bug.',
    resourceId: 'github-deploy',
    status: 'pending',
    riskLevel: 'high',
    requestedAt: '2026-07-16T12:00:00Z',
    expiresAt: '2026-07-17T12:00:00Z',
  };

  it('renders pending approval with action buttons, justification, and details', () => {
    renderWithProviders(<ApprovalCard approval={mockApproval} />);
    
    // Check key fields
    expect(screen.getByText('Deploy package to production')).toBeInTheDocument();
    expect(screen.getByText('coder-agent')).toBeInTheDocument();
    expect(screen.getByText('github-deploy')).toBeInTheDocument();
    expect(screen.getByText('Critical fix for payment gateway authentication bug.')).toBeInTheDocument();
    
    // Check buttons (only present in pending state)
    expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /deny/i })).toBeInTheDocument();
  });

  it('does not render action buttons if status is approved', () => {
    const approvedRequest = { ...mockApproval, status: 'approved' as const };
    renderWithProviders(<ApprovalCard approval={approvedRequest} />);
    
    expect(screen.queryByRole('button', { name: /approve/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /deny/i })).not.toBeInTheDocument();
  });
});
