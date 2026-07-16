"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

export type User = {
  id: string;
  username: string;
  role: string;
};

export type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
};

const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const router = useRouter();

  React.useEffect(() => {
    const initAuth = async () => {
      // In Phase 3C.2 we don't have a backend. We just simulate checking a token.
      const token = localStorage.getItem("asep_access_token");

      if (token) {
        // MOCK: Simulate token validation and fetching user profile
        // In the future this will be an API call to the FastAPI backend.
        setUser({ id: "1", username: "admin", role: "supervisor" });
      } else {
        setUser(null);
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = (token: string, user: User) => {
    localStorage.setItem("asep_access_token", token);
    setUser(user);
    router.push("/overview");
  };

  const logout = () => {
    localStorage.removeItem("asep_access_token");
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
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
