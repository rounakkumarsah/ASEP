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
  GitCommit,
  User,
  ShieldCheck,
  Globe
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";

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

  const fetchLogs = async () => {
    setLoading(true);
    setError("");
    try {
      // Fetch critical audit logs or list logs. Since default list requires parameters, we pull critical ones
      // or fall back to an active audit feed log simulation if empty
      const res = await apiClient.get("/api/v1/audit/critical?days=30");
      setLogs(res.data.items || []);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to load audit logs from server.");
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
        <Card className="border border-dashed p-10 text-center flex flex-col items-center justify-center text-muted-foreground">
          <ShieldCheck className="h-10 w-10 text-emerald-500 mb-2" />
          <CardTitle className="text-base font-bold text-foreground">No audit records</CardTitle>
          <CardDescription className="max-w-xs mt-1">
            No critical audit log trails or failure telemetry are registered in the tracking logs system.
          </CardDescription>
        </Card>
      ) : (
        <div className="relative border-l border-border/40 pl-6 space-y-6 ml-4">
          {filteredLogs.map(log => (
            <div key={log.id} className="relative">
              {/* Point on timeline */}
              <div className="absolute -left-[31px] top-1 h-4 w-4 rounded-full border-2 border-background bg-primary flex items-center justify-center">
                <GitCommit className="h-2 w-2 text-primary-foreground" />
              </div>

              <div className="p-4 border border-border/30 bg-card/15 hover:border-border/65 transition-all rounded-xl space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      log.severity === "high" || log.severity === "critical" ? "bg-red-500/10 text-red-500" : "bg-blue-500/10 text-blue-500"
                    }`}>
                      {log.severity.toUpperCase()}
                    </span>
                    <span className="font-semibold text-sm text-foreground">{log.action}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground">{new Date(log.timestamp).toLocaleString()}</span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-muted-foreground border-t border-border/10 pt-2">
                  <div>
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60">Actor</span>
                    <span className="flex items-center gap-1 mt-0.5">
                      <User className="h-3 w-3" />
                      {log.actor_type.toUpperCase()}: {log.actor_id}
                    </span>
                  </div>
                  <div>
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60">Resource</span>
                    <span className="flex items-center gap-1 mt-0.5">
                      <FileText className="h-3 w-3" />
                      {log.resource_type}
                    </span>
                  </div>
                  <div>
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60">Outcome</span>
                    <span className={`font-semibold ${log.outcome === "success" ? "text-green-500" : "text-red-500"}`}>
                      {log.outcome.toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <span className="block font-semibold text-[10px] uppercase text-muted-foreground/60">Client IP</span>
                    <span className="flex items-center gap-1 mt-0.5">
                      <Globe className="h-3 w-3" />
                      {log.ip_address || "unknown"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
