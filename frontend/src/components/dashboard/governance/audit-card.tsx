import * as React from "react"
import { AuditRecord } from "@/lib/api/types"
import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle2, XCircle, ShieldBan, Terminal } from "lucide-react"
import { cn } from "@/lib/utils"

export function AuditCard({ audit }: { audit: AuditRecord }) {
  const timestamp = new Date(audit.timestamp).toLocaleString(undefined, { 
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit"
  })

  let statusIcon = <CheckCircle2 className="w-4 h-4 text-green-500" />
  let statusColor = "border-l-green-500"
  
  if (audit.status === "failure") {
    statusIcon = <XCircle className="w-4 h-4 text-red-500" />
    statusColor = "border-l-red-500"
  } else if (audit.status === "blocked") {
    statusIcon = <ShieldBan className="w-4 h-4 text-orange-500" />
    statusColor = "border-l-orange-500"
  }

  return (
    <Card className={cn("border-l-4 rounded-lg", statusColor)}>
      <CardContent className="p-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-muted p-2 rounded-md">
            <Terminal className="w-4 h-4 text-muted-foreground" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">{audit.action}</span>
              {statusIcon}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              <span className="font-medium text-foreground">{audit.actor}</span> on <span className="font-medium text-foreground">{audit.target}</span>
            </p>
          </div>
        </div>
        
        <div className="text-right flex flex-col items-end">
          <span className="text-xs tabular-nums text-muted-foreground">{timestamp}</span>
          <span className="text-[10px] uppercase font-bold tracking-wider mt-1 text-muted-foreground/70">{audit.status}</span>
        </div>
      </CardContent>
    </Card>
  )
}
