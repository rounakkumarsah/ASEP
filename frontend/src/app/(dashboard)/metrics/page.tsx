"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { 
  Activity, 
  Cpu, 
  Database, 
  LineChart, 
  Loader2, 
  AlertTriangle,
  RefreshCw,
  Gauge
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

interface MetricsData {
  requests_total: number;
  request_latency_sum: number;
  errors_total: number;
  error_rate: number;
  active_sessions: number;
  pending_tasks: number;
  system: {
    process_memory_rss_bytes: number;
    process_cpu_percent: number;
  };
}

export default function MetricsPage() {
  const [metrics, setMetrics] = React.useState<MetricsData | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [timeFilter, setTimeFilter] = React.useState("1h");

  const fetchMetrics = async () => {
    setLoading(true);
    setError("");
    try {
      // Call endpoint. Since it's mounted at root prefix, we call /metrics
      const res = await apiClient.get("/metrics");
      setMetrics(res.data);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to load real-time system metrics.");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) {
    return (
      <div className="h-[400px] w-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Loading real-time operational telemetry metrics...</p>
      </div>
    );
  }

  const formatBytes = (bytes: number) => {
    if (!bytes) return "0 Bytes";
    const k = 1024;
    const dm = 2;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Telemetry</h1>
          <p className="text-muted-foreground mt-1">
            Real-time system CPU, Memory allocations, and API request latency parameters.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Time range selectors */}
          {["1h", "6h", "24h", "7d"].map(t => (
            <Button
              key={t}
              size="sm"
              variant={timeFilter === t ? "default" : "outline"}
              onClick={() => setTimeFilter(t)}
              className="text-xs font-semibold"
            >
              {t}
            </Button>
          ))}
          <Button size="icon" variant="outline" onClick={fetchMetrics} className="h-9 w-9">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 border border-destructive/20 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {!metrics ? (
        <Card className="border border-dashed p-12 text-center flex flex-col items-center justify-center text-muted-foreground min-h-[400px]">
          <Activity className="h-10 w-10 text-primary/50 mb-4" />
          <CardTitle className="text-xl font-bold text-foreground">No telemetry available yet</CardTitle>
          <CardDescription className="max-w-sm mt-2">
            System operational metrics are not currently being recorded or the monitoring endpoint is inactive.
          </CardDescription>
        </Card>
      ) : (
        <>
          {/* Numerical Metrics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: CPU Util */}
        <Card className="border-border/40 bg-card/30">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">Process CPU</CardTitle>
            <Cpu className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.system?.process_cpu_percent?.toFixed(1) || "0.0"}%</div>
            <p className="text-xs text-muted-foreground mt-1">Process Core Utilization</p>
          </CardContent>
        </Card>

        {/* Card 2: Memory allocations */}
        <Card className="border-border/40 bg-card/30">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">Process RSS Memory</CardTitle>
            <Database className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatBytes(metrics?.system?.process_memory_rss_bytes || 0)}</div>
            <p className="text-xs text-muted-foreground mt-1">Resident Memory Allocation</p>
          </CardContent>
        </Card>

        {/* Card 3: Total requests */}
        <Card className="border-border/40 bg-card/30">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.requests_total || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">API Endpoint Hits</p>
          </CardContent>
        </Card>

        {/* Card 4: Error Rate */}
        <Card className="border-border/40 bg-card/30">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase">API Error Rate</CardTitle>
            <Gauge className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics?.error_rate || 0 * 100).toFixed(2)}%</div>
            <p className="text-xs text-muted-foreground mt-1">HTTP 5xx Server Failures</p>
          </CardContent>
        </Card>

      </div>

      {/* Graphical Details Simulation container */}
      <Card className="border-border/40 bg-card/25">
        <CardHeader>
          <CardTitle className="text-base font-bold">Request Latency Parameters</CardTitle>
          <CardDescription>Average response durations mapping under active workspace loops.</CardDescription>
        </CardHeader>
        <CardContent className="h-[250px] flex items-center justify-center border-t border-border/20">
          <div className="text-center text-muted-foreground space-y-2">
            <LineChart className="h-8 w-8 mx-auto text-primary animate-pulse" />
            <p className="text-xs">Real-time graph metrics update dynamically. Active latency sum: {metrics?.request_latency_sum || 0}s</p>
          </div>
        </CardContent>
      </Card>
      </>
      )}
    </div>
  );
}
