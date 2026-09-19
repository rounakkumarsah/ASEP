"use client";

import * as React from "react";
import { Activity, CheckCircle2, CircleDashed, TerminalSquare, BookOpen, DollarSign, Target, PanelRightClose, RotateCcw, GitBranch, Sparkles, FileText, Compass, Search } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import { useSidebarStore } from "@/lib/stores/sidebarStore";
import { ExplorePanel } from "./ExplorePanel";

export function RightPanel() {
  const {
    messages,
    isThinking,
    activeNode,
    completedNodes,
    sessionMetrics,
    phaseMap,
    githubCommits,
    activeSkills,
    skillCitations,
    explorationEvents,
    phaseExplorations,
    activeRightTab,
    setActiveRightTab,
  } = usePlaygroundStore();
  const { toggleRightPanel } = useSidebarStore();
  const hasActivity = messages.length > 0 || isThinking || completedNodes.length > 0;

  // Extract skills from store or execution trace
  const traceSkills = React.useMemo(() => {
    const list = new Set<string>(activeSkills || []);
    messages.forEach((m) => {
      const match = m.content?.match(/\[SKILL:\s*([^\]]+)\]/i);
      if (match && match[1]) list.add(match[1].trim());
    });
    return Array.from(list);
  }, [messages, activeSkills]);

  // Extract attachment citations from store or execution trace
  const traceCitations = React.useMemo(() => {
    const list = new Set<string>(skillCitations || []);
    messages.forEach((m) => {
      const matches = m.content?.matchAll(/(\[FROM:[^\]]+\])/gi);
      if (matches) {
        for (const match of matches) {
          if (match[1]) list.add(match[1].trim());
        }
      }
    });
    return Array.from(list);
  }, [messages, skillCitations]);

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

  // Extract live tool, web search, and knowledge query events from messages
  const liveToolEvents = React.useMemo(() => {
    const events: Array<{ type: string; text: string }> = [];
    messages.forEach((m) => {
      const c = m.content || "";
      if (c.startsWith("[Web Search]") || c.includes("[Web Search]")) {
        events.push({ type: "SEARCH", text: c.replace(/^.*\[Web Search\]\s*/, "") });
      } else if (c.startsWith("[Knowledge Query]") || c.includes("[Knowledge Query]")) {
        events.push({ type: "KNOWLEDGE", text: c.replace(/^.*\[Knowledge Query\]\s*/, "") });
      } else if (c.startsWith("[Docs Search]") || c.includes("[Docs Search]")) {
        events.push({ type: "DOCS", text: c.replace(/^.*\[Docs Search\]\s*/, "") });
      } else if (c.includes("CALL ") || c.includes("RESP ")) {
        events.push({ type: "TOOL", text: c });
      }
    });
    return events;
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
    { id: "host_manager", label: "Host Manager", desc: "Install deps, start server, health check" },
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
      <div className="p-2 border-b border-border/40 bg-zinc-950/40 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1 bg-muted/40 p-0.5 rounded-lg">
          <Button
            variant={activeRightTab === "trace" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setActiveRightTab("trace")}
            className="h-7 text-xs gap-1.5 px-2.5 font-medium"
          >
            <Activity className="h-3.5 w-3.5 text-[#22D3EE]" />
            Execution Trace
          </Button>
          <Button
            variant={activeRightTab === "explore" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setActiveRightTab("explore")}
            className="h-7 text-xs gap-1.5 px-2.5 font-medium"
          >
            <Compass className="h-3.5 w-3.5 text-cyan-400" />
            Explore Feed
            {explorationEvents.length > 0 && (
              <Badge variant="outline" className="h-4 px-1 text-[9px] bg-cyan-500/10 text-cyan-400 border-cyan-500/30">
                {explorationEvents.length}
              </Badge>
            )}
          </Button>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleRightPanel}
          className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors shrink-0"
          title="Collapse Panel (Ctrl+])"
          aria-label="Collapse Panel"
        >
          <PanelRightClose className="h-4 w-4" />
        </Button>
      </div>

      {activeRightTab === "explore" ? (
        <div className="flex-1 min-h-0">
          <ExplorePanel />
        </div>
      ) : (
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-6">
            
            {/* Execution Timeline */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Plan Timeline</h3>
                {!hasActivity && (
                  <Badge variant="outline" className="text-[9px] font-mono px-1.5 py-0 text-muted-foreground border-border/60 bg-muted/20">
                    Example Trace
                  </Badge>
                )}
              </div>
              
              {!hasActivity ? (
                <div className="relative border-l border-border/60 ml-2 space-y-4 py-2 opacity-60">
                  <div className="absolute -inset-2 bg-gradient-to-b from-transparent via-background/20 to-background z-10 pointer-events-none" />
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
                    const commitSha = githubCommits?.[step.id];
                    const exploreSummary = phaseExplorations?.[step.id];

                    return (
                      <div key={step.id} className={`relative pl-4 transition-all ${!isActive && !isDone ? "opacity-40" : "opacity-100"}`}>
                        {isActive ? (
                          <CircleDashed className="absolute -left-2 top-0 h-4 w-4 text-[#22D3EE] animate-spin bg-background" />
                        ) : isDone ? (
                          <CheckCircle2 className="absolute -left-2 top-0 h-4 w-4 text-emerald-500 bg-background" />
                        ) : (
                          <div className="absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full border-2 border-muted-foreground bg-background" />
                        )}
                        <div className="flex items-center justify-between gap-2">
                          <p className={`text-xs font-medium ${isActive ? "text-[#22D3EE] font-semibold" : isDone ? "text-foreground" : "text-muted-foreground"}`}>
                            {step.label}
                          </p>
                          {isDone && commitSha && (
                            <span
                              className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 shrink-0"
                              title={`GitHub Phase Commit SHA: ${commitSha}`}
                            >
                              <GitBranch className="h-2.5 w-2.5" />
                              {commitSha.slice(0, 7)}
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{step.desc}</p>
                        {isDone && exploreSummary && (
                          <div className="mt-1 text-[9.5px] font-mono text-cyan-400 flex items-center gap-1 bg-cyan-950/20 px-1.5 py-0.5 rounded border border-cyan-500/20">
                            <Search className="h-2.5 w-2.5 shrink-0" />
                            <span>
                              {exploreSummary.files_explored_count} files explored, {exploreSummary.searches_count} searches, ~{Math.round(exploreSummary.tokens_saved / 100) / 10}k tokens
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

            {/* Active Skills in Trace */}
            {traceSkills.length > 0 && (
              <div className="pt-2 border-t border-border/30 space-y-1.5">
                <div className="text-[10px] font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="h-3 w-3 text-purple-400" />
                  Active Skills
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {traceSkills.map((skill) => (
                    <Badge
                      key={skill}
                      variant="outline"
                      className="bg-purple-500/10 text-purple-400 border-purple-500/30 text-[10px] font-mono py-0.5 px-2 flex items-center gap-1"
                    >
                      <Sparkles className="h-2.5 w-2.5 text-purple-400" />
                      [SKILL: {skill}]
                    </Badge>
                  ))}
                </div>
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
                  {healLogs.map((log, idx) => {
                    const hasResearch = log.includes("[Researched:") || log.includes("[Research:");
                    return (
                      <div key={idx} className="p-2 rounded bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 leading-relaxed space-y-1">
                        <span className="text-emerald-400 font-semibold block">{log}</span>
                        {hasResearch && (
                          <div className="flex items-center gap-1.5 text-[9px] text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/20">
                            <Search className="h-2.5 w-2.5 text-cyan-400 shrink-0" />
                            <span>Online Research &amp; Docs Lookup verified before patch</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
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
              {liveToolEvents.length > 0 ? (
                liveToolEvents.map((ev, idx) => (
                  <div key={idx} className="text-muted-foreground flex items-center gap-1.5 truncate">
                    <span className={
                      ev.type === "SEARCH" ? "text-cyan-400 font-bold shrink-0" :
                      ev.type === "KNOWLEDGE" ? "text-purple-400 font-bold shrink-0" :
                      ev.type === "DOCS" ? "text-blue-400 font-bold shrink-0" :
                      "text-emerald-400 font-bold shrink-0"
                    }>
                      [{ev.type}]
                    </span>
                    <span className="truncate text-zinc-300">{ev.text}</span>
                  </div>
                ))
              ) : !hasActivity ? (
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
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Referenced Sources & Attachments</h3>
            {traceCitations.length === 0 && !hasActivity ? (
              <p className="text-xs text-muted-foreground italic">No sources referenced yet.</p>
            ) : (
              <div className="space-y-2">
                {traceCitations.map((citation, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs border border-cyan-500/30 rounded p-2 bg-cyan-950/20 text-cyan-300">
                    <FileText className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                    <span className="font-mono text-[11px] truncate" title={citation}>{citation}</span>
                  </div>
                ))}
                {hasActivity && (
                  <div className="flex items-center gap-2 text-xs border border-border/50 rounded p-2 bg-card/50 hover:bg-card transition-colors cursor-pointer">
                    <BookOpen className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                    <span className="truncate">Next.js App Router Docs</span>
                  </div>
                )}
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
      )}
    </div>
  );
}
