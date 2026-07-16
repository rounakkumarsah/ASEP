import * as React from 'react';
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { AuditCard } from './audit-card';
import { renderWithProviders } from '@/test/utils';
import { AuditRecord } from '@/lib/api/types';

describe('AuditCard Component', () => {
  const mockAudit: AuditRecord = {
    id: 'rec-1',
    timestamp: '2026-07-16T12:00:00Z',
    actor: 'system-agent',
    action: 'Modified policy governance configuration',
    target: 'security-policy',
    status: 'success',
  };

  it('renders success audit record details', () => {
    renderWithProviders(<AuditCard audit={mockAudit} />);
    
    expect(screen.getByText('Modified policy governance configuration')).toBeInTheDocument();
    expect(screen.getByText('system-agent')).toBeInTheDocument();
    expect(screen.getByText('security-policy')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
  });

  it('renders blocked audit record correctly', () => {
    const blockedAudit = { ...mockAudit, status: 'blocked' as const };
    renderWithProviders(<AuditCard audit={blockedAudit} />);
    
    expect(screen.getByText('blocked')).toBeInTheDocument();
  });
});
