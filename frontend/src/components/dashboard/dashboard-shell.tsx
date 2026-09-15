"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/lib/stores/sidebarStore";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { DashboardHeader } from "@/components/dashboard/header";
import { EmailVerificationBanner } from "@/components/dashboard/email-verification-banner";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { isMainSidebarOpen, toggleMainSidebar, toggleLeftPanel, toggleRightPanel } = useSidebarStore();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);

    // Keyboard shortcut handlers:
    // Ctrl/Cmd + B => Toggle Main Sidebar
    // Ctrl/Cmd + [ => Toggle Left Panel (Config)
    // Ctrl/Cmd + ] => Toggle Right Panel (Trace)
    const handleKeyDown = (e: KeyboardEvent) => {
      const isCmdOrCtrl = e.metaKey || e.ctrlKey;
      if (!isCmdOrCtrl) return;

      if (e.key === "b" || e.key === "B") {
        e.preventDefault();
        toggleMainSidebar();
      } else if (e.key === "[") {
        e.preventDefault();
        toggleLeftPanel();
      } else if (e.key === "]") {
        e.preventDefault();
        toggleRightPanel();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleMainSidebar, toggleLeftPanel, toggleRightPanel]);

  // Default to open for SSR
  const isOpen = mounted ? isMainSidebarOpen : true;

  return (
    <div className="min-h-screen bg-background flex w-full">
      {/* Desktop Sidebar */}
      <DashboardSidebar />

      {/* Main Content Column */}
      <div
        className={cn(
          "flex flex-col flex-1 min-h-screen transition-all duration-300 ease-in-out",
          isOpen ? "lg:pl-64" : "lg:pl-0"
        )}
      >
        <DashboardHeader />
        <EmailVerificationBanner />

        <main className="flex-1 w-full">
          <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
