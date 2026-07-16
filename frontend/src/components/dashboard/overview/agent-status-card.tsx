import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot } from "lucide-react";

export function AgentStatusCard({ activeCount }: { activeCount: number }) {
  return (
    <Card className="hover:border-primary/20 transition-colors h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Active Agents
        </CardTitle>
        <Bot className="w-4 h-4 text-primary" />
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-center">
        <div className="text-4xl font-bold tabular-nums">{activeCount}</div>
        <div className="mt-4 flex items-center text-xs text-muted-foreground gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
          </span>
          Routing across{" "}
          <span className="font-semibold text-foreground">3</span> clusters
        </div>
      </CardContent>
    </Card>
  );
}
