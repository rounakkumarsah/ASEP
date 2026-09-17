"use client";

import * as React from "react";
import { Activity, CheckCircle2, CircleDashed, TerminalSquare, BookOpen, DollarSign, Target, PanelRightClose, RotateCcw } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import { useSidebarStore } from "@/lib/stores/sidebarStore";

export function RightPanel() {
  const { messages, isThinking, activeNode, completedNodes, sessionMetrics, phaseMap } = usePlaygroundStore();
  const { toggleRightPanel } = useSidebarStore();
  const hasActivity = messages.length > 0 || isThinking || completedNodes.length > 0;

  // Extract Self-Healing Execution Trace logs
  const healLogs = React.useMemo(() => {
    return messages
      .filter((m) => m.content && (m.content.includes("heal cycle #") || m.content.includes("[Heal Cycle")))
      .map((m) => {
        const text = m.content;
        const match = text.match(/heal cycle #\d+:[^\n]+/i);
        return match ? match[0] : text;
      });
  }, [messages]);

  const DEFAULT_PIPELINE_STEPS = [
    { id: "orchestrator", label: "Orchestrator", desc: "Product classification & phase mapping" },
    { id: "research", label: "Research Phase", desc: "Gather requirements & context" },
    { id: "blueprint", label: "Blueprint Phase", desc: "Architecture & system design" },
    { id: "scaffold", label: "Scaffold Phase", desc: "Boilerplate & foundation setup" },
    { id: "implement", label: "Implement Phase", desc: "Core logic & module construction" },
    { id: "test", label: "Test Phase", desc: "Unit & integration testing" },
    { id: "security_audit", label: "Security Audit", desc: "Vulnerability scanning" },
    { id: "deploy", label: "Deploy Phase", desc: "Release & deployment prep" },
  ];

  let PIPELINE_STEPS = DEFAULT_PIPELINE_STEPS;
  if (phaseMap && phaseMap.length > 0) {
    PIPELINE_STEPS = [
      { id: "orchestrator", label: "Orchestrator", desc: "Product classification & phase mapping" },
      ...phaseMap.map(p => ({
        id: p,
        label: p.split("_").map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ") + " Phase",
        desc: "Execution phase"
      }))
    ];
  }

  return (
    <div className="flex h-full flex-col border-l border-border/40 bg-background/50 backdrop-blur">
      <div className="p-4 pb-2 border-b border-border/40 flex items-center justify-between">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Activity className="h-4 w-4 text-[#22D3EE]" />
          Execution Trace
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleRightPanel}
          className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
          title="Collapse Execution Trace Panel (Ctrl+])"
          aria-label="Collapse Execution Trace Panel"
        >
          <PanelRightClose className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          
          {/* Execution Timeline */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Plan Timeline</h3>
            
            {!hasActivity ? (
              <div className="relative border-l border-border/60 ml-2 space-y-4 py-2 opacity-60">
                <div className="absolute -inset-2 bg-gradient-to-b from-transparent via-background/20 to-background z-10 pointer-events-none" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 text-center w-full">
                  <Badge variant="outline" className="bg-background shadow-lg mb-2 text-[10px]">Example Trace</Badge>
                </div>
                {PIPELINE_STEPS.map((step) => (
                  <div key={step.id} className="relative pl-4 transition-all">
                    <CheckCircle2 className="absolute -left-2 top-0 h-4 w-4 text-emerald-500/50 bg-background" />
                    <p className="text-xs font-medium text-muted-foreground">
                      {step.label}
                    </p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{step.desc}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="relative border-l border-border/60 ml-2 space-y-4 py-2">
                {PIPELINE_STEPS.map((step) => {
                  const isActive = activeNode === step.id;
                  const isDone = completedNodes.includes(step.id) && !isActive;

                  return (
                    <div key={step.id} className={`relative pl-4 transition-all ${!isActive && !isDone ? "opacity-40" : "opacity-100"}`}>
                      {isActive ? (
                        <CircleDashed className="absolute -left-2 top-0 h-4 w-4 text-[#22D3EE] animate-spin bg-background" />
                      ) : isDone ? (
                        <CheckCircle2 className="absolute -left-2 top-0 h-4 w-4 text-emerald-500 bg-background" />
                      ) : (
                        <div className="absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full border-2 border-muted-foreground bg-background" />
                      )}
                      <p className={`text-xs font-medium ${isActive ? "text-[#22D3EE] font-semibold" : isDone ? "text-foreground" : "text-muted-foreground"}`}>
                        {step.label}
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{step.desc}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="h-px bg-border/40" />

          {/* Self-Healing Loop Trace */}
          {healLogs.length > 0 && (
            <>
              <div className="space-y-3">
                <h3 className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <RotateCcw className="h-3.5 w-3.5 text-emerald-400 animate-spin" />
                    Self-Healing Loop
                  </span>
                  <Badge variant="outline" className="text-[9px] h-4 px-1.5 bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                    {healLogs.length} cycle{healLogs.length > 1 ? "s" : ""}
                  </Badge>
                </h3>
                <div className="space-y-1.5 font-mono text-[10px]">
                  {healLogs.map((log, idx) => (
                    <div key={idx} className="p-2 rounded bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 leading-relaxed">
                      <span className="text-emerald-400 font-semibold">{log}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="h-px bg-border/40" />
            </>
          )}

          {/* Tool Calls */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center justify-between">
              Live Tool Logs
              {isThinking && (
                <Badge variant="outline" className="text-[9px] h-4 px-1.5 bg-primary/10 text-primary border-primary/20 animate-pulse">Streaming</Badge>
              )}
            </h3>
            
            <div className="bg-black/50 border border-border/40 rounded-lg p-2 font-mono text-[10px] space-y-1.5 h-32 overflow-y-auto">
              {!hasActivity ? (
                <div className="text-muted-foreground/60 h-full flex flex-col items-center justify-center italic text-center px-4 space-y-2">
                  <TerminalSquare className="h-5 w-5 mb-1 opacity-40" />
                  <p>Awaiting agent execution...</p>
                  <p className="text-[9px] opacity-70">Real-time MCP tool invocations, bash commands, and API requests will stream here.</p>
                </div>
              ) : (
                <>
                  <div className="text-muted-foreground">[{new Date(Date.now() - 5000).toLocaleTimeString()}] <span className="text-emerald-400">CALL</span> list_dir {"{path: '/src/components'}"}</div>
                  <div className="text-muted-foreground">[{new Date(Date.now() - 4000).toLocaleTimeString()}] <span className="text-amber-400">RESP</span> 14 files found.</div>
                  <div className="text-muted-foreground">[{new Date(Date.now() - 2000).toLocaleTimeString()}] <span className="text-emerald-400">CALL</span> read_file {"{path: '/src/components/Button.tsx'}"}</div>
                  <div className="text-muted-foreground flex items-center gap-2">
                    [{new Date().toLocaleTimeString()}] <span className="text-[#22D3EE] animate-pulse">EXEC</span> 
                    <span className="h-1 w-1 bg-[#22D3EE] rounded-full animate-ping" />
                    <span className="h-1 w-1 bg-[#22D3EE] rounded-full animate-ping delay-75" />
                    <span className="h-1 w-1 bg-[#22D3EE] rounded-full animate-ping delay-150" />
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="h-px bg-border/40" />

          {/* Sources */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Referenced Sources</h3>
            {!hasActivity ? (
              <p className="text-xs text-muted-foreground italic">No sources referenced yet.</p>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs border border-border/50 rounded p-2 bg-card/50 hover:bg-card transition-colors cursor-pointer">
                  <BookOpen className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                  <span className="truncate">Next.js App Router Docs</span>
                </div>
              </div>
            )}
          </div>

          <div className="h-px bg-border/40" />

          {/* Metrics */}
          {(hasActivity && (sessionMetrics?.confidence !== null || sessionMetrics?.estimatedCost !== null)) ? (
            <div className="space-y-4">
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Session Metrics</h3>
              
              {sessionMetrics?.confidence !== null && sessionMetrics?.confidence !== undefined && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-muted-foreground"><Target className="h-3.5 w-3.5 text-emerald-400" /> Confidence</span>
                    <span className="font-mono">{Math.round(sessionMetrics.confidence * 100)}%</span>
                  </div>
                  <Progress value={Math.round(sessionMetrics.confidence * 100)} className="h-1.5 bg-emerald-950 [&>div]:bg-emerald-500" />
                </div>
              )}

              {sessionMetrics?.estimatedCost !== null && sessionMetrics?.estimatedCost !== undefined && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="flex items-center gap-1.5 text-muted-foreground"><DollarSign className="h-3.5 w-3.5 text-amber-400" /> Estimated Cost</span>
                    <span className="font-mono">${sessionMetrics.estimatedCost.toFixed(3)}</span>
                  </div>
                  <Progress value={Math.min(100, sessionMetrics.estimatedCost * 1000)} className="h-1.5 bg-amber-950 [&>div]:bg-amber-500" />
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4 opacity-50">
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Session Metrics</h3>
              <p className="text-xs text-muted-foreground italic">Metrics will appear after execution completes.</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
