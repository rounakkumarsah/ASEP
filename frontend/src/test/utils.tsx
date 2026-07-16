import * as React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { AuthContext, AuthContextType } from '@/lib/providers/auth-provider';
import { vi } from 'vitest';

const defaultAuthContextValue: AuthContextType = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
};

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authContextValue?: Partial<AuthContextType>;
}

export function renderWithProviders(
  ui: React.ReactElement,
  { authContextValue, ...options }: CustomRenderOptions = {}
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const mergedAuthContextValue = {
    ...defaultAuthContextValue,
    ...authContextValue,
  };

  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <AuthContext.Provider value={mergedAuthContextValue}>
            {children}
          </AuthContext.Provider>
        </ThemeProvider>
      </QueryClientProvider>
    );
  };

  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  };
}

export * from '@testing-library/react';
