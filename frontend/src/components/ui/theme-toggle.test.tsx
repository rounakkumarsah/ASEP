import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { ThemeToggle } from './theme-toggle';
import { renderWithProviders } from '@/test/utils';
import { useTheme } from 'next-themes';

vi.mock('next-themes', () => {
  const setTheme = vi.fn();
  return {
    useTheme: () => ({
      theme: 'light',
      resolvedTheme: 'light',
      setTheme,
    }),
    ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

describe('ThemeToggle Component', () => {
  it('renders correctly', () => {
    renderWithProviders(<ThemeToggle />);
    const button = screen.getByRole('button', { name: /toggle theme/i });
    expect(button).toBeInTheDocument();
  });

  it('triggers setTheme on click', () => {
    const { setTheme } = useTheme();
    renderWithProviders(<ThemeToggle />);
    const button = screen.getByRole('button', { name: /toggle theme/i });
    
    fireEvent.click(button);
    expect(setTheme).toHaveBeenCalledWith('dark');
  });
});
