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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const router = useRouter();

  const initAuth = async () => {
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
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    initAuth();
  }, []);

  const login = (token: string, userData: User) => {
    setUser(userData);
    router.push("/overview");
  };

  const updateUser = (userData: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...userData } : null));
  };

  const logout = async () => {
    setUser(null);
    router.push("/login");

    try {
      await fetch(`${API_URL}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      console.error("Logout request failed:", e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser: initAuth,
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
