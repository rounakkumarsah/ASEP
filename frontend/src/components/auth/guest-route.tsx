"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/providers/auth-provider";
import { usePathname } from "next/navigation";
import AuthLoadingSkeleton from "@/components/auth/auth-skeleton";
import LoginLoadingSkeleton from "@/components/auth/login-skeleton";

export function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  React.useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/overview");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    if (pathname === "/login") {
      return <LoginLoadingSkeleton />;
    }
    return <AuthLoadingSkeleton />;
  }

  // If authenticated, we render nothing while the useEffect redirects
  if (isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
