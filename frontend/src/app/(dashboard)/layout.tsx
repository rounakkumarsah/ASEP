import { ProtectedRoute } from "@/components/auth/protected-route";
import { QueryProvider } from "@/lib/providers/query-provider";
import { AuthProvider } from "@/lib/providers/auth-provider";
import { DashboardShell } from "@/components/dashboard/dashboard-shell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <QueryProvider>
        <ProtectedRoute>
          <DashboardShell>{children}</DashboardShell>
        </ProtectedRoute>
      </QueryProvider>
    </AuthProvider>
  );
}
