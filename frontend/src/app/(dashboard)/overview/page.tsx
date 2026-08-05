"use client";

import * as React from "react";
import Link from "next/link";
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
  Terminal,
  Cpu,
  RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function OverviewPage() {
  const { user } = useAuth();
  const { data: health, isLoading, isError, refetch } = useSystemOverview();
  const { data: projects } = useProjects();
  const { data: knowledge } = useKnowledge("");

  if (isLoading) {
    return (
      <div className="h-96 w-full flex flex-col items-center justify-center text-[#9CA6B5] space-y-3 font-mono text-xs">
        <Loader2 className="h-6 w-6 animate-spin text-[#22D3EE]" />
        <p>Connecting to ASEP Control Plane telemetry...</p>
      </div>
    );
  }

  if (isError || !health) {
    return (
      <div className="w-full flex flex-col items-center justify-center border border-[#F05252]/30 bg-[#F05252]/5 rounded-xl py-16 text-center space-y-4">
        <p className="font-mono text-sm font-semibold text-[#F05252]">Control Plane Connection Interrupted</p>
        <p className="text-xs text-[#9CA6B5] max-w-md">Unable to establish telemetry stream with the execution orchestrator.</p>
        <Button variant="outline" size="sm" onClick={() => refetch()} className="font-mono text-xs gap-2">
          <RefreshCw className="h-3.5 w-3.5" /> Reconnect Telemetry
        </Button>
      </div>
    );
  }

  // Checklist verification
  const hasProject = (projects?.length || 0) > 0;
  const hasAgent = (health?.activeAgents || 0) > 0;
  const hasKnowledge = (knowledge?.items?.length || 0) > 0;
  const hasChat = (health?.activeSessions || 0) > 0;
  const hasEvaluation = false;
  const hasMonitoring = (health?.activeSessions || 0) > 0;

  const checklist = [
    { label: "Create Project", checked: hasProject, link: "/projects" },
    { label: "Create Agent", checked: hasAgent, link: "/projects" },
    { label: "Upload Knowledge", checked: hasKnowledge, link: "/knowledge" },
    { label: "Start Playground Chat", checked: hasChat, link: "/playground" },
    { label: "Run Evaluation", checked: hasEvaluation, link: "/evaluation" },
    { label: "View Telemetry Metrics", checked: hasMonitoring, link: "/metrics" },
  ];

  const completedCount = checklist.filter(item => item.checked).length;
  const progressPercent = Math.round((completedCount / checklist.length) * 100);

  const isBrandNew = !projects || projects.length === 0;

  return (
    <div className="space-y-6 flex flex-col min-h-full pb-10 w-full">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b border-[#202833] pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="h-5 w-5 text-[#22D3EE]" />
            <h1 className="text-2xl font-bold tracking-tight text-[#F5F7FA] font-mono">Control Plane</h1>
          </div>
          <p className="text-[#9CA6B5] mt-1 text-xs font-mono">
            Autonomous software engineering platform telemetry, operational topology, and agent orchestration.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-[#9CA6B5] bg-[#0D1117] px-3 py-1.5 rounded-lg border border-[#202833]">
          <span className="h-2 w-2 rounded-full bg-[#2DD4A3] animate-pulse" />
          <span>Telemetry Stream Active</span>
        </div>
      </div>

      {isBrandNew ? (
        <div className="space-y-6">
          {/* Welcome Panel */}
          <div className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <h2 className="text-xl font-bold text-[#F5F7FA]">
                Developer Workspace: {user?.first_name || user?.username || "Operator"}
              </h2>
              <p className="text-xs text-[#9CA6B5]">
                Initialize your engineering pipeline by creating a project and orchestrating autonomous code agents.
              </p>
            </div>
            <div className="flex items-center gap-2 bg-[#2DD4A3]/10 text-[#2DD4A3] px-3 py-1 rounded-md text-xs font-mono font-semibold border border-[#2DD4A3]/20">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Workspace Ready</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Onboarding Checklist */}
            <Card className="lg:col-span-2 border-[#202833] bg-[#0D1117] shadow-xs">
              <CardHeader className="pb-3 border-b border-[#202833]">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-bold font-mono text-[#F5F7FA]">Pipeline Onboarding</CardTitle>
                    <CardDescription className="text-xs text-[#9CA6B5]">Configure developer suite parameters</CardDescription>
                  </div>
                  <Badge variant="outline" className="font-mono text-xs py-0.5 border-[#202833] text-[#22D3EE] bg-[#111720]">
                    {progressPercent}% Initialized
                  </Badge>
                </div>
                {/* Progress bar */}
                <div className="w-full bg-[#111720] h-1.5 rounded-full mt-3 overflow-hidden border border-[#202833]">
                  <div 
                    className="bg-[#22D3EE] h-full rounded-full transition-all duration-500" 
                    style={{ width: `${progressPercent}%` }} 
                  />
                </div>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-4">
                {checklist.map((item, index) => (
                  <Link 
                    key={index}
                    href={item.link}
                    className="flex items-center gap-3 p-3 border border-[#202833] rounded-lg bg-[#111720]/40 hover:bg-[#111720] transition-colors"
                  >
                    {item.checked ? (
                      <CheckCircle2 className="h-4 w-4 text-[#2DD4A3] shrink-0" />
                    ) : (
                      <Circle className="h-4 w-4 text-[#667085] shrink-0" />
                    )}
                    <span className={`text-xs font-mono ${item.checked ? "text-[#667085] line-through" : "text-[#F5F7FA]"}`}>
                      {item.label}
                    </span>
                  </Link>
                ))}
              </CardContent>
            </Card>

            {/* Quick Start Card */}
            <Card className="border-[#202833] bg-[#0D1117] shadow-xs flex flex-col justify-between">
              <CardHeader className="border-b border-[#202833]">
                <CardTitle className="text-sm font-bold font-mono text-[#F5F7FA]">Quick Start Guide</CardTitle>
                <CardDescription className="text-xs text-[#9CA6B5]">Deploy your first autonomous project</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 flex-1 flex flex-col justify-between pt-4">
                <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                  ASEP orchestrates coding tasks, runs evaluations against benchmark suites, and logs all execution traces securely.
                </p>
                <Link href="/projects" className="w-full">
                  <Button className="w-full font-mono text-xs font-semibold gap-1.5 bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9]">
                    <span>Create First Project</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity (Empty State) */}
          <Card className="border-[#202833] bg-[#0D1117] shadow-xs">
            <CardHeader className="border-b border-[#202833]">
              <CardTitle className="text-sm font-bold font-mono text-[#F5F7FA]">System Activity Stream</CardTitle>
              <CardDescription className="text-xs text-[#9CA6B5]">Real-time execution log audit trail</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center py-10 text-[#9CA6B5] text-center space-y-2 font-mono">
              <Terminal className="h-8 w-8 text-[#667085]" />
              <p className="font-semibold text-[#F5F7FA] text-xs">No execution logs recorded yet</p>
              <p className="text-[11px] text-[#667085] max-w-sm">
                Activity traces will automatically populate here as agent runs execute.
              </p>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <SystemOverviewCard health={health} />
          <AgentStatusCard activeCount={health.activeAgents} />
          <QueueCard pendingCount={health.pendingApprovals} />

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

          <div className="col-span-full border border-[#202833] rounded-xl bg-[#0D1117] shadow-xs p-5">
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F5F7FA] mb-4">Execution Log Stream</h3>
            <div className="flex flex-col items-center justify-center py-8 text-[#9CA6B5] font-mono text-xs">
              <p>No recent activity traces</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
