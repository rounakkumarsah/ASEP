import * as React from "react";
import { SystemHealth } from "@/lib/api/types";
import { AlertTriangle, XCircle } from "lucide-react";

export function HealthBadge({ status }: { status: SystemHealth["status"] }) {
  if (status === "operational") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-500 text-xs font-medium uppercase tracking-wider">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        Operational
      </div>
    );
  }

  if (status === "degraded") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-yellow-500/20 bg-yellow-500/10 text-yellow-500 text-xs font-medium uppercase tracking-wider">
        <AlertTriangle className="w-3.5 h-3.5" />
        Degraded
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-red-500/20 bg-red-500/10 text-red-500 text-xs font-medium uppercase tracking-wider animate-pulse">
      <XCircle className="w-3.5 h-3.5" />
      Outage
    </div>
  );
}
