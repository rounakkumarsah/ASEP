import * as React from "react"
import { ApprovalRequest } from "@/lib/api/types"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ApprovalStatusBadge } from "./approval-status-badge"
import { RiskBadge } from "./risk-badge"
import { Bot, Target, Clock } from "lucide-react"

export function ApprovalCard({ approval }: { approval: ApprovalRequest }) {
  const requestedAt = new Date(approval.requestedAt).toLocaleString(undefined, { 
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" 
  })

  return (
    <Card className="hover:border-primary/50 transition-colors h-full flex flex-col">
      <CardHeader className="p-4 pb-3 border-b border-border/40 space-y-3">
        <div className="flex items-start justify-between">
          <ApprovalStatusBadge status={approval.status} />
          <RiskBadge level={approval.riskLevel} />
        </div>
        <div className="space-y-1">
          <h3 className="font-semibold text-sm leading-none flex items-center gap-2 text-foreground">
            {approval.requestedAction}
          </h3>
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="w-3 h-3" /> Requested {requestedAt}
          </p>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-4 flex-1 flex flex-col justify-between">
        <div className="space-y-4">
          <div className="space-y-1.5 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Bot className="w-4 h-4" />
              <span className="font-medium text-foreground">{approval.agentId}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Target className="w-4 h-4" />
              <span className="font-medium text-foreground">{approval.resourceId}</span>
            </div>
          </div>
          
          <div className="bg-muted rounded-md p-3 text-sm border">
            <span className="text-muted-foreground font-medium text-xs uppercase tracking-wider mb-1 block">Justification</span>
            <span className="text-foreground">{approval.justification}</span>
          </div>
        </div>

        {approval.status === "pending" && (
          <div className="flex gap-2 mt-4">
            <Button className="w-full" variant="default" size="sm">Approve</Button>
            <Button className="w-full" variant="destructive" size="sm">Deny</Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
