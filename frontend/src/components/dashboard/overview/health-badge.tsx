import * as React from "react";
import { SystemHealth } from "@/lib/api/types";
import { AlertTriangle, XCircle } from "lucide-react";

export function HealthBadge({ status }: { status: SystemHealth["status"] }) {
  if (status === "operational") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-[#2DD4A3]/10 text-[#2DD4A3] border border-[#2DD4A3]/20 uppercase tracking-wider">
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2DD4A3] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#2DD4A3]"></span>
        </span>
        Operational
      </div>
    );
  }

  if (status === "degraded") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-[#F5B942]/10 text-[#F5B942] border border-[#F5B942]/20 uppercase tracking-wider">
        <AlertTriangle className="w-3.5 h-3.5" />
        Degraded
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-[#F05252]/10 text-[#F05252] border border-[#F05252]/20 uppercase tracking-wider animate-pulse">
      <XCircle className="w-3.5 h-3.5" />
      Outage
    </div>
  );
}
