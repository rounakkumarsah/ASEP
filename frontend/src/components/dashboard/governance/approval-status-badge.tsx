import * as React from "react";
import { ApprovalStatus } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, Clock, AlertCircle, Ban } from "lucide-react";

export function ApprovalStatusBadge({ status }: { status: ApprovalStatus }) {
  let icon = <Clock className="w-3.5 h-3.5" />;
  let classes = "bg-muted text-muted-foreground border-border";
  let label = "Unknown";

  switch (status) {
    case "pending":
      icon = <Clock className="w-3.5 h-3.5" />;
      classes = "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
      label = "Pending";
      break;
    case "approved":
      icon = <CheckCircle2 className="w-3.5 h-3.5" />;
      classes = "bg-green-500/10 text-green-500 border-green-500/20";
      label = "Approved";
      break;
    case "denied":
      icon = <XCircle className="w-3.5 h-3.5" />;
      classes = "bg-red-500/10 text-red-500 border-red-500/20";
      label = "Denied";
      break;
    case "expired":
      icon = <AlertCircle className="w-3.5 h-3.5" />;
      classes = "bg-orange-500/10 text-orange-500 border-orange-500/20";
      label = "Expired";
      break;
    case "cancelled":
      icon = <Ban className="w-3.5 h-3.5" />;
      classes = "bg-slate-500/10 text-slate-500 border-slate-500/20";
      label = "Cancelled";
      break;
  }

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-medium uppercase tracking-wider",
        classes,
      )}
    >
      {icon}
      {label}
    </div>
  );
}
