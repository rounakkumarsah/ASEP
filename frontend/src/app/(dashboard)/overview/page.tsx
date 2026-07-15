"use client"

import * as React from "react"
import { useSystemOverview } from "@/lib/api/hooks/use-control-plane"
import { SystemOverviewCard } from "@/components/dashboard/overview/system-overview-card"
import { AgentStatusCard } from "@/components/dashboard/overview/agent-status-card"
import { QueueCard } from "@/components/dashboard/overview/queue-card"
import { MetricCard } from "@/components/dashboard/overview/metric-card"
import { AuditFeedCard } from "@/components/dashboard/overview/audit-feed-card"
import { Loader2, ActivitySquare, BrainCircuit, MessageSquare, Box } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function OverviewPage() {
  const { data: health, isLoading, isError, refetch } = useSystemOverview()

  if (isLoading) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Initializing Control Plane telemetry...</p>
      </div>
    )
  }

  if (isError || !health) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg py-20">
        <p className="font-medium mb-4">Lost connection to Control Plane.</p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>Reconnect</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 flex flex-col min-h-full pb-10">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Control Plane</h1>
          <p className="text-muted-foreground mt-1">
            Global operational state, runtime telemetry, and active agent orchestration.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-card px-3 py-1.5 rounded-full border">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Live connection secured
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Row 1: System Overview and Critical Stats */}
        <SystemOverviewCard health={health} />
        
        <AgentStatusCard activeCount={health.activeAgents} />
        <QueueCard pendingCount={health.pendingApprovals} />

        {/* Row 2: Detailed Metrics */}
        <MetricCard 
          title="Active Sessions" 
          value={health.activeSessions} 
          icon={<ActivitySquare className="w-4 h-4" />} 
          trend={{ value: "2", isPositive: true }}
        />
        
        <MetricCard 
          title="Avg Reflection Cycles" 
          value="4.2" 
          icon={<BrainCircuit className="w-4 h-4" />} 
          trend={{ value: "0.5", isPositive: false }}
        />
        
        <MetricCard 
          title="Inference Tokens" 
          value="1.2M" 
          icon={<MessageSquare className="w-4 h-4" />} 
          trend={{ value: "150k", isPositive: true }}
        />
        
        <MetricCard 
          title="Tool Executions" 
          value="842" 
          icon={<Box className="w-4 h-4" />} 
          trend={{ value: "12", isPositive: true }}
        />

        {/* Row 3: Feeds & Diagnostics */}
        <AuditFeedCard />
        
        <div className="col-span-full lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-dashed rounded-lg flex flex-col items-center justify-center p-8 text-muted-foreground bg-card/30 min-h-[250px]">
            <h3 className="font-semibold text-foreground mb-2">Evaluation Summary</h3>
            <p className="text-sm text-center max-w-[250px]">Evaluation framework is offline. Activate Evaluation node in Control Plane settings.</p>
          </div>
          <div className="border border-dashed rounded-lg flex flex-col items-center justify-center p-8 text-muted-foreground bg-card/30 min-h-[250px]">
            <h3 className="font-semibold text-foreground mb-2">Production Diagnostics</h3>
            <p className="text-sm text-center max-w-[250px]">No active diagnostic traces. System operating within normal parameters.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
