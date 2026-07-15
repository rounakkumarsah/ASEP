"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, ShieldAlert, CheckSquare, Users } from "lucide-react"

export default function DashboardPage() {
  // In Phase 3A, these will eventually fetch from our ControlPlaneAPI via React Query
  const metrics = [
    { title: "Active Sessions", value: "12", icon: Activity },
    { title: "Pending Approvals", value: "3", icon: CheckSquare },
    { title: "Agents Online", value: "5", icon: Users },
    { title: "Recent Errors", value: "0", icon: ShieldAlert },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Overview</h1>
        <p className="text-muted-foreground">
          Monitor your ASEP multi-agent platform and execution metrics.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Execution Throughput (TPS)</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[200px] w-full bg-muted/20 flex items-center justify-center rounded border border-dashed">
              [Chart Placeholder]
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none">Session Complete</p>
                  <p className="text-sm text-muted-foreground">ID: 09fcaaa5-21a9</p>
                </div>
                <div className="ml-auto font-medium">+200ms</div>
              </div>
              <div className="flex items-center">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none">Approval Pending</p>
                  <p className="text-sm text-muted-foreground">Deploy target prod</p>
                </div>
                <div className="ml-auto font-medium text-destructive">Wait</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
