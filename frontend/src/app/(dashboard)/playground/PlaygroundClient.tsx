"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { TopBar } from "@/components/playground/TopBar";
import { LeftPanel } from "@/components/playground/LeftPanel";
import { CenterWorkspace } from "@/components/playground/CenterWorkspace";
import { RightPanel } from "@/components/playground/RightPanel";
import { useSidebarStore } from "@/lib/stores/sidebarStore";
import { PanelLeftOpen, PanelRightOpen } from "lucide-react";

export default function PlaygroundClient() {
  const {
    isMainSidebarOpen,
    isLeftPanelOpen,
    toggleLeftPanel,
    isRightPanelOpen,
    toggleRightPanel,
  } = useSidebarStore();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const mainOpen = mounted ? isMainSidebarOpen : true;
  const leftOpen = mounted ? isLeftPanelOpen : true;
  const rightOpen = mounted ? isRightPanelOpen : true;

  return (
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
          {/* Quick-expand left edge tab when configuration is collapsed */}
          {!leftOpen && (
            <button
              type="button"
              onClick={toggleLeftPanel}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-30 flex items-center gap-1 py-3 px-1.5 rounded-r-md bg-background/90 hover:bg-accent border border-l-0 border-border/60 text-muted-foreground hover:text-primary shadow-lg transition-all group backdrop-blur"
              title="Expand Configuration Panel (Ctrl+[)"
              aria-label="Expand Configuration Panel"
            >
              <PanelLeftOpen className="h-4 w-4 group-hover:scale-110 transition-transform text-primary" />
              <span className="text-[9px] font-mono [writing-mode:vertical-lr] tracking-widest uppercase font-semibold text-muted-foreground group-hover:text-primary">
                Config
              </span>
            </button>
          )}

          <CenterWorkspace />

          {/* Quick-expand right edge tab when execution trace is collapsed */}
          {!rightOpen && (
            <button
              type="button"
              onClick={toggleRightPanel}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-30 flex items-center gap-1 py-3 px-1.5 rounded-l-md bg-background/90 hover:bg-accent border border-r-0 border-border/60 text-muted-foreground hover:text-[#22D3EE] shadow-lg transition-all group backdrop-blur"
              title="Expand Execution Trace Panel (Ctrl+])"
              aria-label="Expand Execution Trace Panel"
            >
              <span className="text-[9px] font-mono [writing-mode:vertical-lr] tracking-widest uppercase font-semibold text-muted-foreground group-hover:text-[#22D3EE]">
                Trace
              </span>
              <PanelRightOpen className="h-4 w-4 group-hover:scale-110 transition-transform text-[#22D3EE]" />
            </button>
          )}
        </main>

        {/* Panel C: Right Sidebar (Execution Trace) */}
        <aside
          className={cn(
            "flex-shrink-0 flex flex-col overflow-hidden bg-background border-l border-border/40 transition-all duration-300 ease-in-out hidden xl:flex",
            rightOpen ? "w-[350px] opacity-100" : "w-0 border-l-0 opacity-0 pointer-events-none"
          )}
        >
          <div className="w-[350px] h-full flex flex-col">
            <RightPanel />
          </div>
        </aside>
      </div>
    </div>
  );
}
