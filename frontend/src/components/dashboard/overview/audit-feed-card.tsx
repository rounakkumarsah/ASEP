import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Terminal, Activity, ArrowRight } from "lucide-react";
import Link from "next/link";

export function AuditFeedCard() {
  const mockActivities = [
    {
      id: 1,
      action: "READ_SECRET api_stripe_key",
      actor: "agent_billing_99",
      time: "5 min ago",
      status: "success",
    },
    {
      id: 2,
      action: "TERMINATE_INSTANCE i-0abcd...",
      actor: "agent_infra_05",
      time: "1 hour ago",
      status: "blocked",
    },
    {
      id: 3,
      action: "UPDATE_MEMORY mem_e_01",
      actor: "agent_core_01",
      time: "2 hours ago",
      status: "success",
    },
  ];

  return (
    <Card className="hover:border-primary/20 transition-colors col-span-full md:col-span-1 lg:col-span-1 flex flex-col h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Recent Audit Activity
        </CardTitle>
        <Activity className="w-4 h-4 text-muted-foreground" />
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between pt-2">
        <div className="space-y-4">
          {mockActivities.map((activity) => (
            <div key={activity.id} className="flex items-start gap-3">
              <div className="mt-0.5 bg-muted p-1.5 rounded-sm">
                <Terminal className="w-3 h-3 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium leading-none truncate max-w-[200px]">
                  {activity.action}
                </p>
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                  <span>{activity.actor}</span>
                  <span>•</span>
                  <span>{activity.time}</span>
                  <span>•</span>
                  <span
                    className={
                      activity.status === "blocked"
                        ? "text-orange-500"
                        : "text-emerald-500"
                    }
                  >
                    {activity.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <Link
          href="/governance?tab=audit"
          className="mt-6 inline-flex items-center text-xs font-medium text-primary hover:underline underline-offset-4 w-fit"
        >
          View all audit logs
          <ArrowRight className="w-3 h-3 ml-1" />
        </Link>
      </CardContent>
    </Card>
  );
}
