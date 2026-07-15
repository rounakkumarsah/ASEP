import * as React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export interface MetricCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: {
    value: string
    isPositive: boolean
  }
  className?: string
}

export function MetricCard({ title, value, icon, trend, className }: MetricCardProps) {
  return (
    <Card className={cn("hover:border-primary/20 transition-colors", className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between space-y-0 pb-2">
          <p className="text-sm font-medium text-muted-foreground tracking-tight">
            {title}
          </p>
          <div className="text-muted-foreground bg-secondary/50 p-2 rounded-md">
            {icon}
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <div className="text-2xl font-bold tabular-nums">
            {value}
          </div>
          {trend && (
            <p className={cn(
              "text-xs font-medium",
              trend.isPositive ? "text-emerald-500" : "text-red-500"
            )}>
              {trend.isPositive ? "+" : "-"}{trend.value} from last hour
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
