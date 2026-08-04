"use client";

import * as React from "react";
import { useSystemOverview } from "@/lib/api/hooks/use-control-plane";
import { useProjects } from "@/lib/api/hooks/use-projects";
import { SystemOverviewCard } from "@/components/dashboard/overview/system-overview-card";
import { AgentStatusCard } from "@/components/dashboard/overview/agent-status-card";
import { QueueCard } from "@/components/dashboard/overview/queue-card";
import { MetricCard } from "@/components/dashboard/overview/metric-card";
import {
  Loader2,
  ActivitySquare,
  BrainCircuit,
  MessageSquare,
  Box,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function OverviewPage() {
  const { data: health, isLoading, isError, refetch } = useSystemOverview();
  const { data: projects } = useProjects();

  if (isLoading) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Initializing Control Plane telemetry...</p>
      </div>
    );
  }

  if (isError || !health) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg py-20">
        <p className="font-medium mb-4">Lost connection to Control Plane.</p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Reconnect
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 flex flex-col min-h-full pb-10">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Control Plane</h1>
          <p className="text-muted-foreground mt-1">
            Global operational state, runtime telemetry, and active agent
            orchestration.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-card px-3 py-1.5 rounded-full border">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Live connection secured
        </div>
      </div>

      {(!projects || projects.length === 0) ? (
        <div className="border border-dashed p-12 text-center flex flex-col items-center justify-center rounded-xl min-h-[350px] bg-card/30">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
            <Box className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-foreground">Welcome to ASEP!</h3>
          <p className="text-sm mt-2 mb-6 text-muted-foreground max-w-sm">
            The Autonomous Software Engineering Platform organizes agent run cycles, evaluations, and memory layers inside Projects. Create your first project to unlock the Control Plane.
          </p>
          <Button onClick={() => window.location.href = "/projects"} className="font-semibold gap-2">
            Create First Project
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Row 1: System Overview and Critical Stats */}
          <SystemOverviewCard health={health} />

          <AgentStatusCard activeCount={health.activeAgents} />
          <QueueCard pendingCount={health.pendingApprovals} />

          {/* Row 2: Detailed Metrics */}
          <MetricCard
            title="Projects"
            value={projects?.length?.toString() || "0"}
            icon={<Box className="w-4 h-4" />}
            trend={{ value: "0", isPositive: true }}
          />

          <MetricCard
            title="Active Sessions"
            value={health?.activeSessions?.toString() || "0"}
            icon={<ActivitySquare className="w-4 h-4" />}
            trend={{ value: "0", isPositive: true }}
          />

          <MetricCard
            title="Active Agents"
            value={health?.activeAgents?.toString() || "0"}
            icon={<BrainCircuit className="w-4 h-4" />}
            trend={{ value: "0", isPositive: true }}
          />

          <MetricCard
            title="Pending Approvals"
            value={health?.pendingApprovals?.toString() || "0"}
            icon={<MessageSquare className="w-4 h-4" />}
            trend={{ value: "0", isPositive: true }}
          />

          {/* Row 3: Feeds & Diagnostics */}
          <div className="col-span-full border rounded-lg bg-card text-card-foreground shadow-sm p-6">
            <h3 className="font-semibold text-lg mb-4">Recent Activity</h3>
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <p>No recent activity</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
