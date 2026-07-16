import * as React from 'react';
import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { ProtectedRoute } from './protected-route';
import { GuestRoute } from './guest-route';
import { renderWithProviders } from '@/test/utils';
import { useRouter } from 'next/navigation';

describe('Auth Routing Components', () => {
  describe('ProtectedRoute', () => {
    it('renders loader while loading', () => {
      renderWithProviders(
        <ProtectedRoute>
          <div>Secret Area</div>
        </ProtectedRoute>,
        {
          authContextValue: { isLoading: true },
        }
      );
      
      expect(screen.queryByText('Secret Area')).not.toBeInTheDocument();
    });

    it('renders children when authenticated', () => {
      renderWithProviders(
        <ProtectedRoute>
          <div>Secret Area</div>
        </ProtectedRoute>,
        {
          authContextValue: { isAuthenticated: true, user: { id: '1', username: 'admin', role: 'supervisor' } },
        }
      );
      
      expect(screen.getByText('Secret Area')).toBeInTheDocument();
    });

    it('redirects to login when unauthenticated', () => {
      const router = useRouter();
      
      renderWithProviders(
        <ProtectedRoute>
          <div>Secret Area</div>
        </ProtectedRoute>,
        {
          authContextValue: { isAuthenticated: false },
        }
      );
      
      expect(screen.queryByText('Secret Area')).not.toBeInTheDocument();
      expect(router.push).toHaveBeenCalled();
    });
  });

  describe('GuestRoute', () => {
    it('renders children when unauthenticated', () => {
      renderWithProviders(
        <GuestRoute>
          <div>Login Page</div>
        </GuestRoute>,
        {
          authContextValue: { isAuthenticated: false },
        }
      );
      
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });

    it('redirects to overview when authenticated', () => {
      const router = useRouter();
      
      renderWithProviders(
        <GuestRoute>
          <div>Login Page</div>
        </GuestRoute>,
        {
          authContextValue: { isAuthenticated: true, user: { id: '1', username: 'admin', role: 'supervisor' } },
        }
      );
      
      expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
      expect(router.push).toHaveBeenCalledWith('/overview');
    });
  });
});
