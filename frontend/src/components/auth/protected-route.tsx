"use client";

import * as React from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/providers/auth-provider";
import DashboardPageSkeleton from "@/components/dashboard/dashboard-skeleton";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Pass the current pathname so we can redirect back after login
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [isLoading, isAuthenticated, router, pathname]);

  // Show dashboard page skeleton loading while determining auth state
  if (isLoading) {
    return <DashboardPageSkeleton />;
  }

  // If not authenticated, we render nothing while the useEffect redirects
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
