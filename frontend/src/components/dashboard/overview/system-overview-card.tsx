import * as React from "react";
import { SystemHealth } from "@/lib/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HealthBadge } from "./health-badge";
import { Server, Cpu, HardDrive } from "lucide-react";

export function SystemOverviewCard({ health }: { health: SystemHealth }) {
  const uptimeDays = Math.floor(health.uptime / 86400);

  return (
    <Card className="col-span-full lg:col-span-2 border-[#202833] bg-[#0D1117] shadow-xs">
      <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-[#202833]">
        <div className="flex items-center gap-2">
          <Server className="w-4 h-4 text-[#22D3EE]" />
          <CardTitle className="text-sm font-bold font-mono tracking-wide uppercase text-[#F5F7FA]">
            System Control Plane
          </CardTitle>
        </div>
        <HealthBadge status={health.status} />
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-1">
            <p className="text-[10px] text-[#9CA6B5] uppercase tracking-wider font-mono font-semibold">
              Platform Uptime
            </p>
            <p className="text-xl font-mono font-bold tabular-nums text-[#F5F7FA] flex items-baseline gap-1">
              {uptimeDays}{" "}
              <span className="text-xs font-normal text-[#667085]">
                days
              </span>
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-[10px] text-[#9CA6B5] uppercase tracking-wider font-mono font-semibold flex items-center gap-1">
                <Cpu className="w-3.5 h-3.5 text-[#22D3EE]" /> CPU Load
              </p>
              <span className="text-xs font-mono font-bold text-[#F5F7FA]">
                {health.cpuUsage}%
              </span>
            </div>
            <div className="h-1.5 w-full bg-[#111720] rounded-full overflow-hidden border border-[#202833]">
              <div
                className="h-full bg-[#22D3EE] transition-all duration-500"
                style={{ width: `${health.cpuUsage}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-[10px] text-[#9CA6B5] uppercase tracking-wider font-mono font-semibold flex items-center gap-1">
                <HardDrive className="w-3.5 h-3.5 text-[#22D3EE]" /> Memory
              </p>
              <span className="text-xs font-mono font-bold text-[#F5F7FA]">
                {health.memoryUsage}%
              </span>
            </div>
            <div className="h-1.5 w-full bg-[#111720] rounded-full overflow-hidden border border-[#202833]">
              <div
                className="h-full bg-[#22D3EE] transition-all duration-500"
                style={{ width: `${health.memoryUsage}%` }}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
