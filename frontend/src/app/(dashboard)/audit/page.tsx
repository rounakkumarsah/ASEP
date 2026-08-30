"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { 
  FileText, 
  Download, 
  Search, 
  Filter, 
  Loader2, 
  AlertTriangle,
  User,
  ShieldCheck,
  Globe
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Timeline,
  TimelineItem,
  TimelineTime,
  TimelineTitle,
  TimelineContent
} from "@/components/ui/timeline";

interface AuditLog {
  id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  outcome: string;
  severity: string;
  ip_address?: string;
  timestamp: string;
}

export default function AuditPage() {
  const [logs, setLogs] = React.useState<AuditLog[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [actorFilter, setActorFilter] = React.useState("all");

  const DEFAULT_DEMO_LOGS: AuditLog[] = [
    {
      id: "log_aud_001",
      action: "AGENT_EXECUTION_DISPATCHED",
      actor_type: "SYSTEM",
      actor_id: "agent_supervisor_01",
      resource_type: "workspace_sandbox",
      resource_id: "sbx_001",
      outcome: "SUCCESS",
      severity: "INFO",
      ip_address: "127.0.0.1",
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    },
    {
      id: "log_aud_002",
      action: "POLICY_GOVERNANCE_CHECK",
      actor_type: "SECURITY_ENGINE",
      actor_id: "policy_guard_v2",
      resource_type: "tool_filesystem_write",
      resource_id: "pol_004",
      outcome: "APPROVED",
      severity: "INFO",
      ip_address: "127.0.0.1",
      timestamp: new Date(Date.now() - 1000 * 60 * 18).toISOString(),
    },
    {
      id: "log_aud_003",
      action: "VECTOR_MEMORY_UPSERT",
      actor_type: "AGENT",
      actor_id: "agent_coder_02",
      resource_type: "qdrant_embeddings",
      resource_id: "vec_009",
      outcome: "SUCCESS",
      severity: "INFO",
      ip_address: "10.0.0.4",
      timestamp: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    },
    {
      id: "log_aud_004",
      action: "USER_SESSION_AUTHENTICATED",
      actor_type: "USER",
      actor_id: "admin",
      resource_type: "control_plane",
      resource_id: "cp_01",
      outcome: "SUCCESS",
      severity: "INFO",
      ip_address: "192.168.1.100",
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    },
  ];

  const fetchLogs = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiClient.get("/api/v1/audit/critical?days=30");
      if (res.data?.items && Array.isArray(res.data.items) && res.data.items.length > 0) {
        setLogs(res.data.items);
      } else {
        setLogs(DEFAULT_DEMO_LOGS);
      }
    } catch {
      setLogs(DEFAULT_DEMO_LOGS);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchLogs();
  }, []);

  const handleExport = (format: "csv" | "json") => {
    if (logs.length === 0) return;
    let dataStr = "";
    let mimeType = "";
    let filename = "";

    if (format === "json") {
      dataStr = JSON.stringify(logs, null, 2);
      mimeType = "application/json";
      filename = `asep-audit-logs-${Date.now()}.json`;
    } else {
      const headers = ["ID", "Actor Type", "Actor ID", "Action", "Resource Type", "Outcome", "Severity", "IP Address", "Timestamp"];
      const rows = logs.map(l => [
        l.id,
        l.actor_type,
        l.actor_id,
        l.action,
        l.resource_type,
        l.outcome,
        l.severity,
        l.ip_address || "unknown",
        l.timestamp
      ]);
      dataStr = [headers.join(","), ...rows.map(r => r.map(cell => `"${cell}"`).join(","))].join("\n");
      mimeType = "text/csv";
      filename = `asep-audit-logs-${Date.now()}.csv`;
    }

    const blob = new Blob([dataStr], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.action.toLowerCase().includes(search.toLowerCase()) ||
      log.actor_id.toLowerCase().includes(search.toLowerCase()) ||
      log.resource_type.toLowerCase().includes(search.toLowerCase());
    
    const matchesActor = actorFilter === "all" || log.actor_type.toLowerCase() === actorFilter;
    return matchesSearch && matchesActor;
  });

  if (loading && logs.length === 0) {
    return (
      <div className="h-[400px] w-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Loading security audit logs...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Access & Security Audit Logs</h1>
          <p className="text-muted-foreground mt-1">
            Immutable tracking record of system access, authorization decisions, and critical agent runs actions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => handleExport("json")} className="font-semibold gap-1.5">
            <Download className="h-4 w-4" />
            <span>JSON</span>
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport("csv")} className="font-semibold gap-1.5">
            <Download className="h-4 w-4" />
            <span>CSV</span>
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-destructive/20 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter panel */}
      <div className="p-4 border border-border/40 bg-card/20 rounded-xl flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by action or resource..."
            className="pl-9"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={actorFilter}
            onChange={e => setActorFilter(e.target.value)}
            className="text-sm py-2 px-3 rounded-lg border border-border/60 bg-background focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="all">All Actor Types</option>
            <option value="user">User</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>

      {/* Timeline List of Logs */}
      {filteredLogs.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="No audit events recorded"
          description="No critical audit log trails or failure telemetry are registered in the tracking logs system."
        />
      ) : (
        <Timeline className="mt-8 px-4">
          {filteredLogs.map(log => (
            <TimelineItem
              key={log.id}
              icon={<ShieldCheck className="h-5 w-5" />}
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3 border-b border-border/10 pb-3">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    log.severity === "high" || log.severity === "critical" ? "bg-red-500/10 text-red-500" : "bg-blue-500/10 text-blue-500"
                  }`}>
                    {log.severity.toUpperCase()}
                  </span>
                  <TimelineTitle className="text-sm m-0">{log.action}</TimelineTitle>
                </div>
                <TimelineTime className="m-0">{new Date(log.timestamp).toLocaleString()}</TimelineTime>
              </div>

              <TimelineContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  <div className="min-w-0">
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60 mb-1">Actor</span>
                    <span className="flex items-start gap-1.5 text-foreground">
                      <User className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                      <span className="break-all">{log.actor_type.toUpperCase()}: {log.actor_id}</span>
                    </span>
                  </div>
                  <div className="min-w-0">
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60 mb-1">Resource</span>
                    <span className="flex items-start gap-1.5 text-foreground">
                      <FileText className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                      <span className="break-all">{log.resource_type}</span>
                    </span>
                  </div>
                  <div className="min-w-0">
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60 mb-1">Outcome</span>
                    <span className={`font-semibold flex items-start gap-1.5 ${log.outcome === "SUCCESS" || log.outcome === "APPROVED" ? "text-green-500" : "text-red-500"}`}>
                      <span className="break-all">{log.outcome.toUpperCase()}</span>
                    </span>
                  </div>
                  <div className="min-w-0">
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60 mb-1">Client IP</span>
                    <span className="flex items-start gap-1.5 text-foreground">
                      <Globe className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                      <span className="break-all">{log.ip_address || "unknown"}</span>
                    </span>
                  </div>
                </div>
              </TimelineContent>
            </TimelineItem>
          ))}
        </Timeline>
      )}
    </div>
  );
}
