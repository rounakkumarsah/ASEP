"use client";

import * as React from "react";
import { useSystemOverview } from "@/lib/api/hooks/use-control-plane";
import { useProjects } from "@/lib/api/hooks/use-projects";
import { useKnowledge } from "@/lib/api/hooks/use-knowledge";
import { useAuth } from "@/lib/providers/auth-provider";
import { SystemOverviewCard } from "@/components/dashboard/overview/system-overview-card";
import { AgentStatusCard } from "@/components/dashboard/overview/agent-status-card";
import { QueueCard } from "@/components/dashboard/overview/queue-card";
import { MetricCard } from "@/components/dashboard/overview/metric-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  ActivitySquare,
  BrainCircuit,
  MessageSquare,
  Box,
  CheckCircle2,
  Circle,
  ArrowRight,
  ShieldCheck,
  Terminal
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function OverviewPage() {
  const { user } = useAuth();
  const { data: health, isLoading, isError, refetch } = useSystemOverview();
  const { data: projects } = useProjects();
  const { data: knowledge } = useKnowledge("");

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

  // Auto-updating checklist criteria
  const hasProject = (projects?.length || 0) > 0;
  const hasAgent = (health?.activeAgents || 0) > 0;
  const hasKnowledge = (knowledge?.items?.length || 0) > 0;
  const hasChat = (health?.activeSessions || 0) > 0;
  const hasEvaluation = false; // Fresh install default
  const hasMonitoring = (health?.activeSessions || 0) > 0;

  const checklist = [
    { label: "Create Project", checked: hasProject, link: "/projects" },
    { label: "Create Agent", checked: hasAgent, link: "/projects" },
    { label: "Upload Knowledge", checked: hasKnowledge, link: "/knowledge" },
    { label: "Start Playground Chat", checked: hasChat, link: "/playground" },
    { label: "Run Evaluation", checked: hasEvaluation, link: "/evaluation" },
    { label: "View Monitoring", checked: hasMonitoring, link: "/metrics" },
  ];

  const completedCount = checklist.filter(item => item.checked).length;
  const progressPercent = Math.round((completedCount / checklist.length) * 100);

  const isBrandNew = !projects || projects.length === 0;

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

      {isBrandNew ? (
        <div className="space-y-6">
          {/* Welcome Message & Account Status */}
          <div className="p-6 border border-border/40 bg-card/25 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <h2 className="text-2xl font-bold text-foreground">
                Welcome back, {user?.first_name || user?.username || "Developer"}!
              </h2>
              <p className="text-sm text-muted-foreground">
                Get started by initializing your workspace and running your first autonomous developer agent.
              </p>
            </div>
            <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-500 px-3 py-1 rounded-full text-xs font-semibold border border-emerald-500/25">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Active Account</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Progress Checklist */}
            <Card className="lg:col-span-2 border-border/40 bg-card/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-bold">Onboarding Checklist</CardTitle>
                    <CardDescription>Follow these steps to configure your developer suite</CardDescription>
                  </div>
                  <Badge variant="secondary" className="font-semibold text-xs py-0.5">
                    {progressPercent}% Complete
                  </Badge>
                </div>
                {/* Progress bar */}
                <div className="w-full bg-muted h-2 rounded-full mt-3 overflow-hidden">
                  <div 
                    className="bg-primary h-full rounded-full transition-all duration-500" 
                    style={{ width: `${progressPercent}%` }} 
                  />
                </div>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                {checklist.map((item, index) => (
                  <div 
                    key={index}
                    onClick={() => window.location.href = item.link}
                    className="flex items-center gap-3 p-3 border border-border/50 rounded-xl hover:bg-accent/40 cursor-pointer transition-colors"
                  >
                    {item.checked ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
                    ) : (
                      <Circle className="h-5 w-5 text-muted-foreground/60 shrink-0" />
                    )}
                    <span className={`text-sm font-medium ${item.checked ? "text-muted-foreground line-through decoration-muted-foreground/40" : "text-foreground"}`}>
                      {item.label}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Quick Start Card */}
            <Card className="border-border/40 bg-card/30 flex flex-col justify-between">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Quick Start Guide</CardTitle>
                <CardDescription>Deploy your first RAG-augmented workspace agent</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 flex-1 flex flex-col justify-between pt-0">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  ASEP coordinates coding tasks, runs evaluations against benchmark suites, and logs all network and file system executions securely.
                </p>
                <Button onClick={() => window.location.href = "/projects"} className="w-full font-semibold gap-1.5 mt-4">
                  <span>Create First Project</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity (Empty state) */}
          <Card className="border-border/40 bg-card/30">
            <CardHeader>
              <CardTitle className="text-lg font-bold">Recent Workspace Activity</CardTitle>
              <CardDescription>Real-time log of agent tasks and access credentials audit trail</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center py-10 text-muted-foreground text-center">
              <Terminal className="h-10 w-10 text-muted-foreground/50 mb-3" />
              <p className="font-semibold text-foreground text-sm">No activity recorded yet</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                Activity event records will automatically populate here once agent tasks are executed.
              </p>
            </CardContent>
          </Card>
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
