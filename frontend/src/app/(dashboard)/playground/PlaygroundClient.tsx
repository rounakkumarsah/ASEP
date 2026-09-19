"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { TopBar } from "@/components/playground/TopBar";
import { LeftPanel } from "@/components/playground/LeftPanel";
import { CenterWorkspace } from "@/components/playground/CenterWorkspace";
import { RightPanel } from "@/components/playground/RightPanel";
import { useSidebarStore } from "@/lib/stores/sidebarStore";

// Inline error boundary to surface the REAL error message instead of generic "Something went wrong!"
class PlaygroundErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null; errorInfo: React.ErrorInfo | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ error, errorInfo });
    // Log full details to console for debugging
    console.error("[Playground Error Boundary] Caught error:", error);
    console.error("[Playground Error Boundary] Component stack:", errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen w-full flex-col items-center justify-center space-y-4 bg-[#090B0F] px-4 text-center font-mono">
          <div className="space-y-2 max-w-2xl w-full text-left">
            <h1 className="text-xl font-bold tracking-tight text-red-400">
              🚨 Playground Runtime Error
            </h1>
            <div className="bg-[#0D1117] border border-red-500/30 rounded-lg p-4 space-y-3">
              <div>
                <p className="text-[11px] text-[#9CA6B5] uppercase tracking-wider mb-1">Error Type</p>
                <p className="text-sm text-red-400 font-mono">{this.state.error?.name}: {this.state.error?.message}</p>
              </div>
              <div>
                <p className="text-[11px] text-[#9CA6B5] uppercase tracking-wider mb-1">Stack Trace</p>
                <pre className="text-[10px] text-[#667085] overflow-auto max-h-40 bg-black/30 p-2 rounded whitespace-pre-wrap">
                  {this.state.error?.stack}
                </pre>
              </div>
              {this.state.errorInfo?.componentStack && (
                <div>
                  <p className="text-[11px] text-[#9CA6B5] uppercase tracking-wider mb-1">React Component Stack</p>
                  <pre className="text-[10px] text-[#667085] overflow-auto max-h-32 bg-black/30 p-2 rounded whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              )}
            </div>
            <button
              onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
              className="mt-4 px-4 py-2 bg-[#22D3EE]/10 border border-[#22D3EE]/30 text-[#22D3EE] rounded-lg text-xs hover:bg-[#22D3EE]/20 transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function PlaygroundClient() {
  const {
    isMainSidebarOpen,
    isLeftPanelOpen,
    isRightPanelOpen,
  } = useSidebarStore();
  const [mounted, setMounted] = React.useState(false);
  const [apiErrorToast, setApiErrorToast] = React.useState<{ message: string; retry?: () => void } | null>(null);

  React.useEffect(() => {
    setMounted(true);
    
    const handleApiError = (e: Event) => {
      const customEvent = e as CustomEvent;
      setApiErrorToast({
        message: customEvent.detail.message || "Network request failed",
        retry: customEvent.detail.retry
      });
      // Auto-dismiss after 10s if not retried
      setTimeout(() => setApiErrorToast(null), 10000);
    };

    window.addEventListener("api:error", handleApiError);
    return () => window.removeEventListener("api:error", handleApiError);
  }, []);

  const mainOpen = mounted ? isMainSidebarOpen : false;
  const leftOpen = mounted ? isLeftPanelOpen : true;
  const rightOpen = mounted ? isRightPanelOpen : true;

  return (
    <PlaygroundErrorBoundary>
      <div
        className={cn(
          "fixed inset-0 top-14 flex flex-col bg-background text-foreground overflow-hidden z-10 transition-all duration-300 ease-in-out",
          mainOpen ? "lg:left-64" : "lg:left-0"
        )}
      >
        <React.Suspense fallback={<div className="h-14 border-b border-border/40 bg-background/95" />}>
          <TopBar />
        </React.Suspense>
        <div className="flex flex-1 overflow-hidden relative">
          {/* Panel A: Left Sidebar (Configuration) */}
          <aside
            className={cn(
              "flex-shrink-0 flex flex-col overflow-hidden bg-background border-r border-border/40 transition-all duration-300 ease-in-out hidden md:flex",
              leftOpen ? "w-[320px] opacity-100" : "w-0 border-r-0 opacity-0 pointer-events-none"
            )}
          >
            <div className="w-[320px] h-full flex flex-col">
              <LeftPanel />
            </div>
          </aside>

          {/* Panel B: Center Workspace */}
          <main className="flex-1 h-full flex flex-col min-w-0 bg-background relative overflow-hidden">
            <CenterWorkspace />
          </main>

          {/* Panel C: Right Sidebar (Execution Trace) */}
          <aside
            className={cn(
              "flex-shrink-0 flex flex-col overflow-hidden bg-background border-l border-border/40 transition-all duration-300 ease-in-out hidden xl:flex",
              rightOpen ? "w-[420px] opacity-100" : "w-0 border-l-0 opacity-0 pointer-events-none"
            )}
          >
            <div className="w-[420px] h-full flex flex-col">
              <RightPanel />
            </div>
          </aside>
        </div>

        {apiErrorToast && (
          <div className="fixed bottom-6 right-6 z-50 flex items-center gap-4 bg-destructive text-destructive-foreground px-4 py-3 rounded-md shadow-lg animate-in slide-in-from-bottom-5">
            <div className="text-sm font-medium">{apiErrorToast.message}</div>
            <div className="flex gap-2">
              {apiErrorToast.retry && (
                <button
                  onClick={() => {
                    apiErrorToast.retry!();
                    setApiErrorToast(null);
                  }}
                  className="px-2 py-1 bg-background/20 hover:bg-background/30 rounded text-xs transition-colors"
                >
                  Retry
                </button>
              )}
              <button
                onClick={() => setApiErrorToast(null)}
                className="px-2 py-1 bg-background/20 hover:bg-background/30 rounded text-xs transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}
      </div>
    </PlaygroundErrorBoundary>
  );
}
