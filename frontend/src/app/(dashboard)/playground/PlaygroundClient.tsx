"use client";

import * as React from "react";
import { TopBar } from "@/components/playground/TopBar";
import { LeftPanel } from "@/components/playground/LeftPanel";
import { CenterWorkspace } from "@/components/playground/CenterWorkspace";
import { RightPanel } from "@/components/playground/RightPanel";

export default function PlaygroundClient() {
  return (
    <div className="fixed inset-0 lg:left-64 top-14 flex flex-col bg-background text-foreground overflow-hidden z-10">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        {/* Panel A: Left Sidebar (Config) - Fixed Width */}
        <aside className="w-[320px] flex-shrink-0 flex flex-col overflow-hidden bg-background hidden md:flex">
          <LeftPanel />
        </aside>

        {/* Panel B: Center Workspace - Flexible Width */}
        <main className="flex-1 flex flex-col min-w-0 bg-background relative overflow-hidden">
          <CenterWorkspace />
        </main>

        {/* Panel C: Right Sidebar (Agent Trace) - Fixed Width */}
        <aside className="w-[350px] flex-shrink-0 flex flex-col overflow-hidden bg-background hidden xl:flex">
          <RightPanel />
        </aside>
      </div>
    </div>
  );
}
