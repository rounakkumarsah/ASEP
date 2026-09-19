"use client";

import * as React from "react";
import {
  Search,
  FileText,
  Brain,
  Wrench,
  Check,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  Code,
  Sparkles,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { usePlaygroundStore, ExplorationSummary } from "@/lib/stores/playgroundStore";

export function ExplorePanel() {
  const {
    explorationEvents,
    phaseExplorations,
    setActiveCenterTab,
    isThinking,
  } = usePlaygroundStore();

  const [activeFilter, setActiveFilter] = React.useState<"all" | "search" | "read" | "think">("all");
  const [expandedEvents, setExpandedEvents] = React.useState<Record<string, boolean>>({});
  const [showRawJson, setShowRawJson] = React.useState(false);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);
  const [liveElapsedSec, setLiveElapsedSec] = React.useState(0);
  const [isSummaryOpen, setIsSummaryOpen] = React.useState(true);

  const scrollBottomRef = React.useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = React.useState(true);

  // Live timer for ongoing actions
  React.useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isThinking) {
      const start = Date.now();
      timer = setInterval(() => {
        setLiveElapsedSec(Math.round(((Date.now() - start) / 1000) * 10) / 10);
      }, 200);
    } else {
      setLiveElapsedSec(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isThinking]);

  // Auto-scroll to bottom on new events if autoScroll is enabled
  React.useEffect(() => {
    if (autoScroll && scrollBottomRef.current) {
      scrollBottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
    }
  }, [explorationEvents, autoScroll]);

  // Filter events
  const filteredEvents = React.useMemo(() => {
    const list = explorationEvents.slice(-500);
    if (activeFilter === "all") return list;
    if (activeFilter === "search") return list.filter((e) => e.type === "search");
    if (activeFilter === "read") return list.filter((e) => e.type === "read");
    if (activeFilter === "think") return list.filter((e) => e.type === "think" || e.type === "analyze");
    return list;
  }, [explorationEvents, activeFilter]);

  const searchCount = React.useMemo(() => explorationEvents.filter((e) => e.type === "search").length, [explorationEvents]);
  const readCount = React.useMemo(() => explorationEvents.filter((e) => e.type === "read").length, [explorationEvents]);
  const thinkCount = React.useMemo(() => explorationEvents.filter((e) => e.type === "think" || e.type === "analyze").length, [explorationEvents]);

  // Latest summary
  const latestSummary: ExplorationSummary | null = React.useMemo(() => {
    const keys = Object.keys(phaseExplorations);
    if (keys.length === 0) return null;
    return phaseExplorations[keys[keys.length - 1]] || null;
  }, [phaseExplorations]);

  const toggleExpand = (id: string) => {
    setExpandedEvents((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopyRaw = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex h-full flex-col bg-[#090B0F] font-mono text-xs text-zinc-300">
      {/* Header & Filter Controls */}
      <div className="p-3 border-b border-border/40 bg-zinc-950/80 backdrop-blur flex flex-col gap-2.5">
        {/* Row 1: Title & Controls */}
        <div className="flex flex-wrap items-center justify-between gap-y-2 gap-x-3">
          <div className="flex items-center gap-2 shrink-0">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
            </span>
            <span className="font-semibold text-zinc-100 uppercase tracking-wider text-[11px] whitespace-nowrap">
              Live Exploration Feed
            </span>
            <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30 text-[10px] px-1.5 py-0 h-4 font-mono shrink-0">
              {explorationEvents.length} events
            </Badge>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowRawJson((prev) => !prev)}
              className={`h-6 text-[10px] px-2 font-mono border rounded transition-colors ${
                showRawJson
                  ? "border-cyan-500/50 bg-cyan-500/15 text-cyan-300 shadow-[0_0_8px_rgba(34,211,238,0.2)]"
                  : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
              }`}
              title="Toggle raw event JSON view"
            >
              <Code className="h-3 w-3 mr-1" />
              {showRawJson ? "Formatted" : "Raw JSON"}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setAutoScroll((prev) => !prev)}
              className={`h-6 text-[10px] px-2 font-mono border rounded transition-colors ${
                autoScroll
                  ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400"
                  : "border-zinc-800 bg-zinc-900/50 text-zinc-500 hover:bg-zinc-800"
              }`}
              title="Toggle terminal auto-scroll"
            >
              <span className={`h-1.5 w-1.5 rounded-full mr-1 ${autoScroll ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}`} />
              Auto-Scroll: {autoScroll ? "ON" : "OFF"}
            </Button>
          </div>
        </div>

        {/* Row 2: Segmented Filter Controls */}
        <div className="grid grid-cols-4 gap-1 p-0.5 bg-zinc-900/80 rounded-lg border border-zinc-800/60 font-mono text-[10px]">
          <button
            onClick={() => setActiveFilter("all")}
            className={`py-1 px-1 rounded-md text-[10px] transition-all flex items-center justify-center gap-1 ${
              activeFilter === "all"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-medium shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border border-transparent"
            }`}
          >
            <span>All</span>
            <span className="text-[9px] opacity-75 font-mono">({explorationEvents.length})</span>
          </button>
          <button
            onClick={() => setActiveFilter("search")}
            className={`py-1 px-1 rounded-md text-[10px] transition-all flex items-center justify-center gap-1 ${
              activeFilter === "search"
                ? "bg-blue-500/20 text-blue-300 border border-blue-500/40 font-medium shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border border-transparent"
            }`}
          >
            <Search className="h-2.5 w-2.5 shrink-0" />
            <span>Searches</span>
            <span className="text-[9px] opacity-75 font-mono">({searchCount})</span>
          </button>
          <button
            onClick={() => setActiveFilter("read")}
            className={`py-1 px-1 rounded-md text-[10px] transition-all flex items-center justify-center gap-1 ${
              activeFilter === "read"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-medium shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border border-transparent"
            }`}
          >
            <FileText className="h-2.5 w-2.5 shrink-0" />
            <span>Files</span>
            <span className="text-[9px] opacity-75 font-mono">({readCount})</span>
          </button>
          <button
            onClick={() => setActiveFilter("think")}
            className={`py-1 px-1 rounded-md text-[10px] transition-all flex items-center justify-center gap-1 ${
              activeFilter === "think"
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 font-medium shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border border-transparent"
            }`}
          >
            <Brain className="h-2.5 w-2.5 shrink-0" />
            <span>Thoughts</span>
            <span className="text-[9px] opacity-75 font-mono">({thinkCount})</span>
          </button>
        </div>
      </div>

      {/* Main Terminal Feed */}
      <ScrollArea className="flex-1 p-3">
        <div className="space-y-2 pb-6">
          {filteredEvents.length === 0 ? (
            <div className="h-72 flex flex-col items-center justify-center text-center p-6 space-y-3">
              <div className="h-12 w-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shadow-[0_0_24px_rgba(34,211,238,0.12)]">
                <Brain className="h-6 w-6 opacity-80 animate-pulse" />
              </div>
              <div className="space-y-1 max-w-[260px]">
                <p className="font-semibold text-zinc-200 text-xs">
                  Awaiting exploration actions...
                </p>
                <p className="text-[10px] opacity-70 text-zinc-400 leading-relaxed">
                  Live search, file reads, timed thoughts, and summaries will stream here.
                </p>
              </div>
              <div className="pt-2 w-full max-w-[270px] space-y-1.5 text-left">
                <div className="p-2 rounded-lg bg-zinc-900/60 border border-zinc-800/80 flex items-center gap-2 text-[10px] text-zinc-400">
                  <Search className="h-3 w-3 text-blue-400 shrink-0" />
                  <span>Codebase search & symbols</span>
                </div>
                <div className="p-2 rounded-lg bg-zinc-900/60 border border-zinc-800/80 flex items-center gap-2 text-[10px] text-zinc-400">
                  <FileText className="h-3 w-3 text-amber-400 shrink-0" />
                  <span>Targeted 20-line file previews</span>
                </div>
                <div className="p-2 rounded-lg bg-zinc-900/60 border border-zinc-800/80 flex items-center gap-2 text-[10px] text-zinc-400">
                  <Brain className="h-3 w-3 text-purple-400 shrink-0" />
                  <span>Real-time multi-agent reasoning</span>
                </div>
              </div>
            </div>
          ) : (
            filteredEvents.map((ev, idx) => {
              const isExpanded = !!expandedEvents[ev.id];
              const isLast = idx === filteredEvents.length - 1;
              const isLongRunning = isLast && isThinking && liveElapsedSec > 15;

              return (
                <div
                  key={ev.id}
                  className={`rounded border transition-all p-2 ${
                    ev.status === "failed"
                      ? "bg-rose-950/20 border-rose-500/30 text-rose-300"
                      : ev.type === "think" || ev.type === "analyze"
                      ? "bg-purple-950/15 border-purple-500/25 text-purple-200"
                      : ev.type === "search"
                      ? "bg-blue-950/15 border-blue-500/25 text-blue-200"
                      : "bg-zinc-900/60 border-zinc-800 text-zinc-200"
                  }`}
                >
                  {/* Event Header Line */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-[10px] text-zinc-500 shrink-0 font-mono">
                        [{ev.timestamp}]
                      </span>

                      {/* Event Icon */}
                      {ev.type === "search" ? (
                        <span className="p-0.5 rounded bg-blue-500/10 text-blue-400 shrink-0">
                          <Search className="h-3.5 w-3.5" />
                        </span>
                      ) : ev.type === "read" ? (
                        <span className="p-0.5 rounded bg-amber-500/10 text-amber-400 shrink-0">
                          <FileText className="h-3.5 w-3.5" />
                        </span>
                      ) : ev.type === "think" || ev.type === "analyze" ? (
                        <span className="p-0.5 rounded bg-purple-500/10 text-purple-400 shrink-0">
                          <Brain className="h-3.5 w-3.5" />
                        </span>
                      ) : (
                        <span className="p-0.5 rounded bg-zinc-800 text-zinc-400 shrink-0">
                          <Wrench className="h-3.5 w-3.5" />
                        </span>
                      )}

                      {/* Detail Text */}
                      <span className="font-mono text-[11px] truncate" title={ev.detail}>
                        {ev.detail}
                      </span>

                      {/* Match Count Badge */}
                      {ev.match_count !== undefined && ev.match_count !== null && (
                        <Badge variant="outline" className="text-[9px] px-1 py-0 h-4 bg-blue-500/10 text-blue-400 border-blue-500/30">
                          {ev.match_count} match{ev.match_count === 1 ? "" : "es"}
                        </Badge>
                      )}

                      {/* Failed Warning Badge */}
                      {ev.status === "failed" && (
                        <Badge variant="outline" className="text-[9px] px-1 py-0 h-4 bg-rose-500/20 text-rose-400 border-rose-500/40 flex items-center gap-0.5">
                          <AlertTriangle className="h-2.5 w-2.5" />
                          Failed (retrying)
                        </Badge>
                      )}
                    </div>

                    {/* Status & Duration Badge */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      {ev.status === "running" ? (
                        <span className="flex items-center gap-1 text-[10px] text-cyan-400 font-mono">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          {isLongRunning ? (
                            <span className="text-amber-400 animate-pulse font-bold">
                              ({liveElapsedSec}s live ⚠️)
                            </span>
                          ) : (
                            <span>({liveElapsedSec > 0 ? liveElapsedSec : (ev.duration_ms / 1000).toFixed(1)}s)</span>
                          )}
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[10px] text-zinc-400 font-mono">
                          <Check className="h-3 w-3 text-emerald-400" />
                          <span>({(ev.duration_ms / 1000).toFixed(1)}s)</span>
                        </span>
                      )}

                      {/* File preview toggle button */}
                      {ev.content_preview && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => toggleExpand(ev.id)}
                          className="h-5 w-5 text-zinc-400 hover:text-zinc-100"
                          title="Toggle file preview"
                        >
                          {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Inline 20-line File Preview */}
                  {ev.content_preview && isExpanded && (
                    <div className="mt-2 pt-2 border-t border-zinc-800/80 space-y-1.5">
                      <div className="flex items-center justify-between text-[10px] text-zinc-400">
                        <span className="flex items-center gap-1 font-mono">
                          <FileText className="h-3 w-3 text-amber-400" />
                          {ev.file}
                          {ev.size_bytes ? ` • ${roundBytes(ev.size_bytes)}` : ""}
                        </span>
                        <Button
                          variant="link"
                          size="sm"
                          onClick={() => setActiveCenterTab("artifacts")}
                          className="h-5 p-0 text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                        >
                          Read full file in Artifacts
                          <ExternalLink className="h-2.5 w-2.5" />
                        </Button>
                      </div>

                      {/* 20 lines code block */}
                      <pre className="p-2 bg-black/60 rounded border border-zinc-800 text-[10px] font-mono text-zinc-300 overflow-x-auto max-h-48 leading-relaxed">
                        {ev.content_preview.split("\n").map((line, lIdx) => (
                          <div key={lIdx} className="flex gap-2">
                            <span className="text-zinc-600 select-none w-6 text-right shrink-0">{lIdx + 1}</span>
                            <span>{line}</span>
                          </div>
                        ))}
                      </pre>
                    </div>
                  )}

                  {/* Error detail */}
                  {ev.error && (
                    <div className="mt-1 text-[10px] text-rose-400 font-mono">
                      Error: {ev.error}
                    </div>
                  )}

                  {/* Raw JSON toggle per event */}
                  {showRawJson && (
                    <div className="mt-2 pt-2 border-t border-zinc-800/80">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[9px] text-zinc-500 uppercase">Event JSON</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopyRaw(JSON.stringify(ev, null, 2), ev.id)}
                          className="h-4 px-1 text-[9px] text-zinc-400 hover:text-zinc-100"
                        >
                          {copiedId === ev.id ? <Check className="h-2.5 w-2.5 text-emerald-400 mr-1" /> : <Copy className="h-2.5 w-2.5 mr-1" />}
                          {copiedId === ev.id ? "Copied" : "Copy"}
                        </Button>
                      </div>
                      <pre className="p-1.5 bg-black/80 rounded text-[9px] text-zinc-400 overflow-x-auto max-h-32">
                        {JSON.stringify(ev, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}

          {/* Bottom marker for auto-scroll */}
          <div ref={scrollBottomRef} />
        </div>
      </ScrollArea>

      {/* Exploration Summary Card */}
      {latestSummary && (
        <div className="p-3 border-t border-border/40 bg-zinc-950/80 backdrop-blur">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
              <span className="font-semibold text-zinc-200 uppercase tracking-wider text-[10px]">
                Exploration Summary ({latestSummary.phase})
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 text-[9px] h-4">
                ~{latestSummary.tokens_saved.toLocaleString()} tokens spared
              </Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsSummaryOpen((prev) => !prev)}
                className="h-5 w-5 text-zinc-400"
              >
                {isSummaryOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              </Button>
            </div>
          </div>

          {isSummaryOpen && (
            <div className="space-y-2 bg-zinc-900/50 p-2.5 rounded border border-zinc-800 text-[10px]">
              <div className="grid grid-cols-3 gap-2 py-1 border-b border-zinc-800/60 text-center">
                <div>
                  <div className="text-zinc-500 text-[9px]">Files Explored</div>
                  <div className="font-bold text-zinc-200">{latestSummary.files_explored_count}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-[9px]">Searches</div>
                  <div className="font-bold text-zinc-200">{latestSummary.searches_count}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-[9px]">Time Spent</div>
                  <div className="font-bold text-zinc-200">{(latestSummary.duration_ms / 1000).toFixed(1)}s</div>
                </div>
              </div>

              <div>
                <span className="text-zinc-400 font-semibold">Architecture Understanding:</span>
                <p className="text-zinc-300 mt-0.5 leading-relaxed">{latestSummary.architecture_understanding}</p>
              </div>

              {latestSummary.risks_identified && latestSummary.risks_identified.length > 0 && (
                <div>
                  <span className="text-amber-400 font-semibold flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    Identified Risks & Mitigations:
                  </span>
                  <ul className="list-disc list-inside mt-0.5 text-zinc-300 space-y-0.5">
                    {latestSummary.risks_identified.map((risk, rIdx) => (
                      <li key={rIdx}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}

              {latestSummary.relevant_files && latestSummary.relevant_files.length > 0 && (
                <div className="pt-1 border-t border-zinc-800/60">
                  <span className="text-zinc-400 font-semibold">Discovered Modules:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {latestSummary.relevant_files.map((file, fIdx) => (
                      <span key={fIdx} className="bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono text-[9px] border border-zinc-700">
                        {file}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function roundBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
