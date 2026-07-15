import { DashboardSidebar } from "@/components/dashboard/sidebar"
import { DashboardHeader } from "@/components/dashboard/header"
import { ProtectedRoute } from "@/components/auth/protected-route"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background flex w-full">
        {/* Desktop Sidebar */}
        <DashboardSidebar />
        
        {/* Main Content Column */}
        <div className="lg:pl-64 flex flex-col flex-1 min-h-screen">
          <DashboardHeader />
          
          <main className="flex-1 w-full">
            <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
              {children}
            </div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
