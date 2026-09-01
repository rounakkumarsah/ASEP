"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

export type User = {
  id: string;
  username: string;
  email?: string;
  role: string;
  first_name?: string | null;
  last_name?: string | null;
  company?: string | null;
  avatar_url?: string | null;
  email_verified?: boolean;
  mfa_enabled?: boolean;
  account_type?: string | null;
  timezone?: string | null;
  locale?: string | null;
  current_plan?: string | null;
};

export type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
};

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

const API_URL = "";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const router = useRouter();

  const initAuth = async () => {
    // Check localStorage first for demo/active session
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("asep_user_session");
      if (stored) {
        try {
          const parsedUser = JSON.parse(stored);
          setUser(parsedUser);
          setIsLoading(false);
          return;
        } catch {
          localStorage.removeItem("asep_user_session");
        }
      }
    }

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
        if (typeof window !== "undefined") {
          localStorage.setItem("asep_user_session", JSON.stringify(userData));
        }
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = React.useCallback(async () => {
    setUser(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("asep_user_session");
      localStorage.removeItem("asep_auth_token");
    }
    router.push("/login");

    try {
      await fetch(`${API_URL}/api/v1/auth/logout`, { method: "POST" });
    } catch {
      // ignore
    }
  }, [router]);

  React.useEffect(() => {
    initAuth();
  }, []);

  React.useEffect(() => {
    const handleUnauthorized = () => logout();
    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", handleUnauthorized);
  }, [logout]);

  const login = (token: string, userData: User) => {
    setUser(userData);
    if (typeof window !== "undefined") {
      localStorage.setItem("asep_user_session", JSON.stringify(userData));
      if (token) {
        localStorage.setItem("asep_auth_token", token);
      }
    }
    router.push("/overview");
  };

  const updateUser = (userData: Partial<User>) => {
    setUser((prev) => {
      if (!prev) return null;
      const updated = { ...prev, ...userData };
      if (typeof window !== "undefined") {
        localStorage.setItem("asep_user_session", JSON.stringify(updated));
      }
      return updated;
    });
  };

  const refreshUser = async () => {
    await initAuth();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
