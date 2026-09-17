"use client";

import * as React from "react";
import {
  Compass,
  Search,
  FileCode,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Coins,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExplorationSummary, usePlaygroundStore } from "@/lib/stores/playgroundStore";
import { useSidebarStore } from "@/lib/stores/sidebarStore";

interface ExplorationCardProps {
  content?: string;
  summary?: ExplorationSummary;
}

export function ExplorationCard({ content, summary: propSummary }: ExplorationCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const { setActiveRightTab } = usePlaygroundStore();
  const { setRightPanelOpen } = useSidebarStore();

  const summary: ExplorationSummary | null = React.useMemo(() => {
    if (propSummary) return propSummary;
    if (!content) return null;
    try {
      const clean = content.replace(/^\[Explore Summary\]\s*/, "").trim();
      return JSON.parse(clean);
    } catch {
      return null;
    }
  }, [content, propSummary]);

  if (!summary) {
    return null;
  }

  const handleOpenExploreFeed = () => {
    setActiveRightTab("explore");
    setRightPanelOpen(true);
  };

  const tokensSparedLabel =
    summary.tokens_saved >= 1000
      ? `~${(summary.tokens_saved / 1000).toFixed(1)}k tokens spared`
      : `~${summary.tokens_saved} tokens spared`;

  return (
    <div className="my-3 rounded-xl border border-cyan-500/30 bg-card/90 shadow-sm overflow-hidden transition-all hover:border-cyan-500/50">
      {/* Header bar */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-cyan-950/40 via-background to-cyan-950/20 cursor-pointer select-none border-b border-cyan-900/30"
      >
        <div className="flex items-center gap-2.5 flex-wrap min-w-0">
          <div className="h-7 w-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center shrink-0">
            <Compass className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold tracking-wide text-foreground">
              Exploration Phase:
            </span>
            <Badge
              variant="outline"
              className="text-[11px] font-mono capitalize bg-cyan-950/40 border-cyan-700/50 text-cyan-300"
            >
              {summary.phase}
            </Badge>
            <span className="text-xs text-muted-foreground">•</span>
            <span className="text-xs text-muted-foreground font-mono">
              {summary.files_explored_count} files explored
            </span>
            <span className="text-xs text-muted-foreground">•</span>
            <span className="text-xs text-muted-foreground font-mono">
              {summary.searches_count} searches
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 ml-2">
          <Badge
            variant="outline"
            className="text-[10px] font-mono bg-emerald-950/40 border-emerald-500/40 text-emerald-300 flex items-center gap-1 shadow-sm"
          >
            <Coins className="h-3 w-3 text-emerald-400" />
            <span>{tokensSparedLabel}</span>
          </Badge>
          <button
            type="button"
            className="p-1 rounded text-muted-foreground hover:text-foreground transition-colors"
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-cyan-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Expandable Body */}
      {isExpanded && (
        <div className="p-4 space-y-4 text-xs animate-in fade-in duration-200">
          {/* Architecture Understanding */}
          {summary.architecture_understanding && (
            <div className="space-y-1.5">
              <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                <Search className="h-3.5 w-3.5" />
                <span>Architecture Understanding</span>
              </div>
              <p className="text-muted-foreground leading-relaxed bg-muted/20 border border-border/40 rounded-lg p-3 font-sans">
                {summary.architecture_understanding}
              </p>
            </div>
          )}

          {/* Risks Identified */}
          {summary.risks_identified && summary.risks_identified.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>Risks Identified ({summary.risks_identified.length})</span>
              </div>
              <ul className="space-y-1 bg-amber-950/20 border border-amber-900/40 rounded-lg p-3">
                {summary.risks_identified.map((risk, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-amber-200/90 text-[11px]">
                    <span className="text-amber-500 mt-0.5">•</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Discovered Relevant Files */}
          {summary.relevant_files && summary.relevant_files.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <FileCode className="h-3.5 w-3.5" />
                <span>Discovered Modules & Files ({summary.relevant_files.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto pr-1">
                {summary.relevant_files.map((file, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-muted/40 border border-border/40 text-foreground/90 hover:border-cyan-500/40 transition-colors"
                  >
                    <FileCode className="h-2.5 w-2.5 text-cyan-400" />
                    {file}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action footer: Open Live Explore Feed */}
          <div className="pt-2 border-t border-border/40 flex items-center justify-between">
            <span className="text-[10px] text-muted-foreground">
              Exploration actions are recorded in real-time
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={handleOpenExploreFeed}
              className="h-7 text-xs gap-1.5 border-cyan-500/40 text-cyan-300 hover:text-cyan-200 hover:bg-cyan-950/40"
            >
              <Compass className="h-3.5 w-3.5 text-cyan-400" />
              <span>Open Live Explore Feed</span>
              <ExternalLink className="h-3 w-3 opacity-60" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
