import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  className?: string;
}

export function MetricCard({
  title,
  value,
  icon,
  trend,
  className,
}: MetricCardProps) {
  return (
    <Card
      className={cn("border-[#202833] bg-[#0D1117] shadow-xs", className)}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between space-y-0 pb-2">
          <p className="text-xs font-mono font-semibold uppercase tracking-wider text-[#9CA6B5]">
            {title}
          </p>
          <div className="text-[#22D3EE] bg-[#111720] p-1.5 rounded-md border border-[#202833]">
            {icon}
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <div className="text-2xl font-mono font-bold tabular-nums text-[#F5F7FA]">{value}</div>
          {trend && (
            <p
              className={cn(
                "text-[10px] font-mono font-medium",
                trend.isPositive ? "text-[#2DD4A3]" : "text-[#F05252]",
              )}
            >
              {trend.isPositive ? "+" : "-"}
              {trend.value} active status
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
