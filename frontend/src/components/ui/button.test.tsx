import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { Button } from './button';
import { renderWithProviders } from '@/test/utils';

describe('Button Component', () => {
  it('renders children correctly', () => {
    renderWithProviders(<Button>Click Me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('handles click events', () => {
    const onClick = vi.fn();
    renderWithProviders(<Button onClick={onClick}>Click Me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('respects disabled state', () => {
    const onClick = vi.fn();
    renderWithProviders(<Button onClick={onClick} disabled>Click Me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeDisabled();
    
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });
});
