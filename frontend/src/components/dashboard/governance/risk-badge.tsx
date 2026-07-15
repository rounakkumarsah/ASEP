import * as React from "react"
import { RiskLevel } from "@/lib/api/types"
import { ShieldAlert, Shield, ShieldCheck, AlertTriangle } from "lucide-react"

export function RiskBadge({ level }: { level: RiskLevel }) {
  let icon = <Shield className="w-3.5 h-3.5" />
  let classes = "text-muted-foreground"
  let label = "Unknown"

  switch (level) {
    case "low":
      icon = <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
      classes = "text-foreground font-medium"
      label = "Low Risk"
      break
    case "medium":
      icon = <AlertTriangle className="w-3.5 h-3.5 text-yellow-500" />
      classes = "text-foreground font-medium"
      label = "Medium Risk"
      break
    case "high":
      icon = <ShieldAlert className="w-3.5 h-3.5 text-orange-500" />
      classes = "text-foreground font-semibold"
      label = "High Risk"
      break
    case "critical":
      icon = <ShieldAlert className="w-3.5 h-3.5 text-red-500 animate-pulse" />
      classes = "text-foreground font-bold"
      label = "Critical Risk"
      break
  }

  return (
    <div className="flex items-center gap-1.5 text-xs">
      {icon}
      <span className={classes}>{label}</span>
    </div>
  )
}
