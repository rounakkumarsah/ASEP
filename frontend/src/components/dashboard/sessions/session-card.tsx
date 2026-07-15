import * as React from "react"
import Link from "next/link"
import { Session } from "@/lib/api/types"
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { SessionStatusBadge } from "./session-status-badge"
import { Clock, Bot, Activity } from "lucide-react"

export function SessionCard({ session }: { session: Session }) {
  const startedAtDate = new Date(session.startedAt)
  const timeElapsed = Math.floor((Date.now() - startedAtDate.getTime()) / 60000)

  return (
    <Link href={`/sessions/${session.sessionId}`}>
      <Card className="hover:bg-muted/40 transition-colors cursor-pointer group h-full flex flex-col">
        <CardHeader className="pb-3 border-b border-border/50">
          <div className="flex items-start justify-between">
            <div className="space-y-1.5">
              <CardTitle className="text-base font-semibold font-mono tracking-tight group-hover:text-primary transition-colors">
                {session.sessionId}
              </CardTitle>
              <div className="flex items-center text-xs text-muted-foreground gap-3">
                <span className="flex items-center gap-1">
                  <Activity className="h-3.5 w-3.5" />
                  {session.runId}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {timeElapsed > 0 ? `${timeElapsed}m ago` : 'Just now'}
                </span>
              </div>
            </div>
            <SessionStatusBadge status={session.status} />
          </div>
        </CardHeader>
        <CardContent className="pt-4 flex-1 flex flex-col">
          <div className="space-y-3 flex-1">
            <div className="flex justify-between items-center text-sm">
              <span className="font-medium text-foreground">Stage</span>
              <span className="text-muted-foreground">{session.stage}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="font-medium text-foreground flex items-center gap-1.5">
                <Bot className="h-4 w-4 text-primary" /> Active Agent
              </span>
              <span className="text-muted-foreground">{session.activeAgent}</span>
            </div>
          </div>
          
          <div className="mt-6 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground truncate pr-4">{session.currentTask}</span>
              <span className="font-medium tabular-nums">{session.progress}%</span>
            </div>
            <Progress value={session.progress} className="h-1.5" />
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
