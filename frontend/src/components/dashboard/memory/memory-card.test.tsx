import * as React from 'react';
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { MemoryCard } from './memory-card';
import { renderWithProviders } from '@/test/utils';
import { MemoryItem } from '@/lib/api/types';

describe('MemoryCard Component', () => {
  const mockItem: MemoryItem = {
    id: 'm1',
    type: 'working',
    content: 'This is a test of the working memory system.',
    tags: ['test', 'unit', 'frontend', 'coverage'],
    confidence: 0.952,
    createdAt: '2026-07-16T12:00:00Z',
  };

  it('renders memory label, content, confidence, and tags', () => {
    renderWithProviders(<MemoryCard item={mockItem} />);
    
    // Check type label mapping
    expect(screen.getByText('Working Memory')).toBeInTheDocument();
    
    // Check main content
    expect(screen.getByText('This is a test of the working memory system.')).toBeInTheDocument();
    
    // Check tags (only first 3 should render as text, then +1 badge)
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('unit')).toBeInTheDocument();
    expect(screen.getByText('frontend')).toBeInTheDocument();
    expect(screen.getByText('+1')).toBeInTheDocument();
    expect(screen.queryByText('coverage')).not.toBeInTheDocument(); // shouldn't render because slice is (0,3)
    
    // Check confidence score
    expect(screen.getByText('Confidence')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
  });
});
