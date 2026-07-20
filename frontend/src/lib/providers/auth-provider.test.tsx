import * as React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './auth-provider';
import { renderWithProviders } from '@/test/utils';
import { useRouter } from 'next/navigation';

const TestComponent = () => {
  const { user, isAuthenticated, login, logout, isLoading } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  return (
    <div>
      {isAuthenticated ? (
        <div>
          <span>Authenticated as {user?.username}</span>
          <button onClick={logout}>Logout</button>
        </div>
      ) : (
        <div>
          <span>Guest</span>
          <button onClick={() => login('token123', { id: '1', username: 'tester', role: 'admin' })}>
            Login
          </button>
        </div>
      )}
    </div>
  );
};

describe('AuthProvider and useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    // Reset global fetch mock
    global.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({}),
      })
    );
  });

  it('initially resolves unauthenticated state when no token is present', async () => {
    renderWithProviders(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // After mount/effects resolved
    const guestText = await screen.findByText('Guest');
    expect(guestText).toBeInTheDocument();
  });

  it('initially resolves authenticated state when server returns user details', async () => {
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.endsWith('/api/v1/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: '1', username: 'admin', role: 'supervisor' }),
        });
      }
      return Promise.resolve({ ok: false });
    });

    renderWithProviders(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const authText = await screen.findByText('Authenticated as admin');
    expect(authText).toBeInTheDocument();
  });

  it('performs login correctly', async () => {
    const router = useRouter();
    renderWithProviders(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await screen.findByText('Guest');
    const loginButton = screen.getByRole('button', { name: /login/i });
    
    await act(async () => {
      loginButton.click();
    });

    expect(screen.getByText('Authenticated as tester')).toBeInTheDocument();
    expect(router.push).toHaveBeenCalledWith('/overview');
  });

  it('performs logout correctly', async () => {
    const router = useRouter();
    
    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.endsWith('/api/v1/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: '1', username: 'admin', role: 'supervisor' }),
        });
      }
      if (url.endsWith('/api/v1/auth/logout')) {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({ ok: false });
    });

    renderWithProviders(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await screen.findByText('Authenticated as admin');
    const logoutButton = screen.getByRole('button', { name: /logout/i });
    
    await act(async () => {
      logoutButton.click();
    });

    expect(screen.getByText('Guest')).toBeInTheDocument();
    expect(router.push).toHaveBeenCalledWith('/login');
  });
});
