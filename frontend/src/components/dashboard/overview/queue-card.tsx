import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldAlert, ArrowRight } from "lucide-react";
import Link from "next/link";

export function QueueCard({ pendingCount }: { pendingCount: number }) {
  const hasPending = pendingCount > 0;

  return (
    <Card
      className={`hover:border-primary/20 transition-colors h-full flex flex-col ${hasPending ? "border-orange-500/30 bg-orange-500/5" : ""}`}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Approval Queue
        </CardTitle>
        <ShieldAlert
          className={`w-4 h-4 ${hasPending ? "text-orange-500" : "text-muted-foreground"}`}
        />
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-center">
        <div className="text-4xl font-bold tabular-nums">{pendingCount}</div>

        <Link
          href="/governance?tab=approvals"
          className="mt-4 inline-flex items-center text-xs font-medium text-primary hover:underline underline-offset-4 w-fit"
        >
          {hasPending ? "Review pending actions" : "View governance policies"}
          <ArrowRight className="w-3 h-3 ml-1" />
        </Link>
      </CardContent>
    </Card>
  );
}
