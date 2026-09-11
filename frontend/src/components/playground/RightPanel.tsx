"use client";

import * as React from "react";
import { Activity, Clock, CheckCircle2, CircleDashed, TerminalSquare, BookOpen, Link as LinkIcon, DollarSign, Target } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export function RightPanel() {
  return (
    <div className="flex h-full flex-col border-l border-border/40 bg-background/50 backdrop-blur">
      <div className="p-4 pb-2 border-b border-border/40">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Activity className="h-4 w-4 text-[#22D3EE]" />
          Execution Trace
        </h2>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          
          {/* Execution Timeline */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Plan Timeline</h3>
            <div className="relative border-l border-border/60 ml-2 space-y-4 py-2">
              <div className="relative pl-4">
                <CheckCircle2 className="absolute -left-2 top-0 h-4 w-4 text-emerald-500 bg-background" />
                <p className="text-xs font-medium text-foreground">Planner Agent</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">Analyzed request & formed strategy</p>
              </div>
              <div className="relative pl-4">
                <CheckCircle2 className="absolute -left-2 top-0 h-4 w-4 text-emerald-500 bg-background" />
                <p className="text-xs font-medium text-foreground">Repo Search</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">Scanned 14 files in /src</p>
              </div>
              <div className="relative pl-4">
                <CircleDashed className="absolute -left-2 top-0 h-4 w-4 text-[#22D3EE] animate-spin-slow bg-background" />
                <p className="text-xs font-medium text-[#22D3EE]">Code Generation</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">Writing implementation...</p>
              </div>
              <div className="relative pl-4 opacity-50">
                <div className="absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full border-2 border-muted-foreground bg-background" />
                <p className="text-xs font-medium text-foreground">Security Audit</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">Pending</p>
              </div>
            </div>
          </div>

          <div className="h-px bg-border/40" />

          {/* Tool Calls */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center justify-between">
              Live Tool Logs
              <Badge variant="outline" className="text-[9px] h-4 px-1.5 bg-primary/10 text-primary border-primary/20">Streaming</Badge>
            </h3>
            <div className="bg-black/50 border border-border/40 rounded-lg p-2 font-mono text-[10px] space-y-1.5 h-32 overflow-y-auto">
              <div className="text-muted-foreground">[{new Date().toLocaleTimeString()}] <span className="text-emerald-400">CALL</span> list_dir {"{path: '/src/components'}"}</div>
              <div className="text-muted-foreground">[{new Date().toLocaleTimeString()}] <span className="text-amber-400">RESP</span> 14 files found.</div>
              <div className="text-muted-foreground">[{new Date().toLocaleTimeString()}] <span className="text-emerald-400">CALL</span> read_file {"{path: 'page.tsx'}"}</div>
              <div className="text-muted-foreground">[{new Date().toLocaleTimeString()}] <span className="text-amber-400">RESP</span> 1200 lines read.</div>
              <div className="text-muted-foreground">[{new Date().toLocaleTimeString()}] <span className="text-[#22D3EE]">EXEC</span> Generating AST...</div>
            </div>
          </div>

          <div className="h-px bg-border/40" />

          {/* Sources */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Referenced Sources</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs border border-border/50 rounded p-2 bg-card/50 hover:bg-card transition-colors cursor-pointer">
                <BookOpen className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                <span className="truncate">Next.js App Router Docs</span>
              </div>
              <div className="flex items-center gap-2 text-xs border border-border/50 rounded p-2 bg-card/50 hover:bg-card transition-colors cursor-pointer">
                <LinkIcon className="h-3.5 w-3.5 text-purple-400 shrink-0" />
                <span className="truncate">Knowledge Base: UI Patterns</span>
              </div>
            </div>
          </div>

          <div className="h-px bg-border/40" />

          {/* Metrics */}
          <div className="space-y-4">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Session Metrics</h3>
            
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="flex items-center gap-1.5 text-muted-foreground"><Target className="h-3.5 w-3.5 text-emerald-400" /> Confidence</span>
                <span className="font-mono">94%</span>
              </div>
              <Progress value={94} className="h-1.5 bg-emerald-950 [&>div]:bg-emerald-500" />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="flex items-center gap-1.5 text-muted-foreground"><DollarSign className="h-3.5 w-3.5 text-amber-400" /> Estimated Cost</span>
                <span className="font-mono">$0.042</span>
              </div>
              <Progress value={15} className="h-1.5 bg-amber-950 [&>div]:bg-amber-500" />
            </div>
          </div>

        </div>
      </ScrollArea>
    </div>
  );
}
