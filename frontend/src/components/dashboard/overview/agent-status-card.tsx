import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot } from "lucide-react";

export function AgentStatusCard({ activeCount }: { activeCount: number }) {
  return (
    <Card className="border-[#202833] bg-[#0D1117] shadow-xs flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-[#202833]/50">
        <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-[#9CA6B5]">
          Active Agents
        </CardTitle>
        <Bot className="w-4 h-4 text-[#22D3EE]" />
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-center pt-4">
        <div className="text-3xl font-mono font-bold tabular-nums text-[#F5F7FA]">{activeCount}</div>
        <div className="mt-3 flex items-center text-[11px] font-mono text-[#9CA6B5] gap-2">
          {activeCount > 0 && (
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#22D3EE] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#22D3EE]"></span>
            </span>
          )}
          <span>{activeCount > 0 ? "Orchestrating agent tasks" : "No active agent executions"}</span>
        </div>
      </CardContent>
    </Card>
  );
}
