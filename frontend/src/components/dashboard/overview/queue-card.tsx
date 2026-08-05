import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldAlert, ArrowRight } from "lucide-react";
import Link from "next/link";

export function QueueCard({ pendingCount }: { pendingCount: number }) {
  const hasPending = pendingCount > 0;

  return (
    <Card
      className={`border-[#202833] bg-[#0D1117] shadow-xs flex flex-col ${hasPending ? "border-[#F5B942]/30 bg-[#F5B942]/5" : ""}`}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-[#202833]/50">
        <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-[#9CA6B5]">
          Approval Queue
        </CardTitle>
        <ShieldAlert
          className={`w-4 h-4 ${hasPending ? "text-[#F5B942]" : "text-[#667085]"}`}
        />
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-center pt-4">
        <div className="text-3xl font-mono font-bold tabular-nums text-[#F5F7FA]">{pendingCount}</div>

        <Link
          href="/approvals"
          className="mt-3 inline-flex items-center text-[11px] font-mono font-medium text-[#22D3EE] hover:underline underline-offset-4 w-fit"
        >
          <span>{hasPending ? "Review pending approvals" : "View governance policies"}</span>
          <ArrowRight className="w-3 h-3 ml-1" />
        </Link>
      </CardContent>
    </Card>
  );
}
