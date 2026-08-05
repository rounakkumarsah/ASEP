import * as React from "react";
import { MemoryItem } from "@/lib/api/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Zap, BrainCircuit, Library, Briefcase, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

function getMemoryConfig(type: MemoryItem["type"]) {
  switch (type) {
    case "working":
      return {
        icon: Zap,
        color: "text-[#38BDF8]",
        bg: "bg-[#38BDF8]/10",
        label: "Working Memory",
      };
    case "episodic":
      return {
        icon: Activity,
        color: "text-[#22D3EE]",
        bg: "bg-[#22D3EE]/10",
        label: "Episodic Memory",
      };
    case "semantic":
      return {
        icon: Library,
        color: "text-[#2DD4A3]",
        bg: "bg-[#2DD4A3]/10",
        label: "Semantic Memory",
      };
    case "procedural":
      return {
        icon: Briefcase,
        color: "text-[#F5B942]",
        bg: "bg-[#F5B942]/10",
        label: "Procedural Memory",
      };
    default:
      return {
        icon: BrainCircuit,
        color: "text-[#22D3EE]",
        bg: "bg-[#22D3EE]/10",
        label: "Unknown",
      };
  }
}

export function MemoryCard({ item }: { item: MemoryItem }) {
  const config = getMemoryConfig(item.type);
  const Icon = config.icon;

  const date = new Date(item.createdAt).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Card className="border-[#202833] bg-[#0D1117] hover:border-[#22D3EE]/40 transition-colors h-full flex flex-col shadow-xs">
      <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between border-b border-[#202833]">
        <div className="flex items-center gap-2">
          <div className={cn("p-1.5 rounded-md border border-[#202833]", config.bg)}>
            <Icon className={cn("h-4 w-4", config.color)} />
          </div>
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#9CA6B5]">
            {config.label}
          </span>
        </div>
        <span className="text-xs font-mono text-[#667085] tabular-nums">
          {date}
        </span>
      </CardHeader>

      <CardContent className="p-4 pt-4 flex-1 flex flex-col">
        <p className="text-xs text-[#F5F7FA] leading-relaxed flex-1 font-sans">
          {item.content}
        </p>

        <div className="mt-4 flex items-center justify-between">
          <div className="flex gap-1.5 flex-wrap">
            {item.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded bg-[#111720] border border-[#202833] px-2 py-0.5 text-[10px] font-mono text-[#9CA6B5]"
              >
                {tag}
              </span>
            ))}
            {item.tags.length > 3 && (
              <span className="inline-flex items-center rounded bg-[#111720] border border-[#202833] px-2 py-0.5 text-[10px] font-mono text-[#667085]">
                +{item.tags.length - 3}
              </span>
            )}
          </div>

          {item.confidence && (
            <div className="flex flex-col items-end">
              <span className="text-[10px] font-mono text-[#667085] uppercase">
                Confidence
              </span>
              <span className="text-xs font-mono font-semibold text-[#22D3EE] tabular-nums">
                {Math.round(item.confidence * 100)}%
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
