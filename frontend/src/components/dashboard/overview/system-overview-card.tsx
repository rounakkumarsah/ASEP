import * as React from "react"
import { SystemHealth } from "@/lib/api/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { HealthBadge } from "./health-badge"
import { Server, Cpu, MemoryStick } from "lucide-react"

export function SystemOverviewCard({ health }: { health: SystemHealth }) {
  const uptimeDays = Math.floor(health.uptime / 86400)
  
  return (
    <Card className="col-span-full lg:col-span-2 hover:border-primary/20 transition-colors bg-gradient-to-br from-card to-card/50">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-primary" />
          <CardTitle className="text-lg">System Overview</CardTitle>
        </div>
        <HealthBadge status={health.status} />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Uptime</p>
            <p className="text-2xl font-bold tabular-nums flex items-baseline gap-1">
              {uptimeDays} <span className="text-sm font-normal text-muted-foreground">days</span>
            </p>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold flex items-center gap-1">
                <Cpu className="w-3.5 h-3.5" /> CPU Load
              </p>
              <span className="text-xs font-bold tabular-nums">{health.cpuUsage}%</span>
            </div>
            <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-1000 ease-in-out" 
                style={{ width: `${health.cpuUsage}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold flex items-center gap-1">
                <MemoryStick className="w-3.5 h-3.5" /> Memory
              </p>
              <span className="text-xs font-bold tabular-nums">{health.memoryUsage}%</span>
            </div>
            <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-1000 ease-in-out" 
                style={{ width: `${health.memoryUsage}%` }}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
