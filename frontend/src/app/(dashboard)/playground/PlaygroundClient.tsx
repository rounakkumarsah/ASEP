"use client";

import * as React from "react";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { TopBar } from "@/components/playground/TopBar";
import { LeftPanel } from "@/components/playground/LeftPanel";
import { CenterWorkspace } from "@/components/playground/CenterWorkspace";
import { RightPanel } from "@/components/playground/RightPanel";

export default function PlaygroundClient() {
  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col overflow-hidden bg-background">
      <TopBar />
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup
          direction="horizontal"
          className="h-full w-full items-stretch"
        >
          <ResizablePanel defaultSize={20} minSize={15} maxSize={30} className="hidden md:block">
            <LeftPanel />
          </ResizablePanel>
          <ResizableHandle withHandle className="bg-border/50 hidden md:flex" />
          <ResizablePanel defaultSize={60} minSize={30}>
            <CenterWorkspace />
          </ResizablePanel>
          <ResizableHandle withHandle className="bg-border/50 hidden xl:flex" />
          <ResizablePanel defaultSize={20} minSize={15} maxSize={30} className="hidden xl:block">
            <RightPanel />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  );
}
