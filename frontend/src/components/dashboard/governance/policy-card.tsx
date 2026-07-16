import * as React from "react";
import { GovernancePolicy } from "@/lib/api/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "./risk-badge";
import { FileWarning } from "lucide-react";

export function PolicyCard({ policy }: { policy: GovernancePolicy }) {
  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="p-4 pb-2 border-b border-border/40">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <FileWarning className="w-4 h-4 text-primary" />
            <h3 className="font-semibold text-sm leading-none">
              {policy.name}
            </h3>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={policy.isActive}
            className={`
              peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50
              ${policy.isActive ? "bg-primary" : "bg-input"}
            `}
          >
            <span
              className={`
                pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform
                ${policy.isActive ? "translate-x-4" : "translate-x-0"}
              `}
            />
          </button>
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-3 space-y-4">
        <p className="text-sm text-muted-foreground leading-relaxed">
          {policy.description}
        </p>

        <div className="flex items-center justify-between border-t pt-3">
          <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
            Risk Threshold
          </span>
          <RiskBadge level={policy.riskThreshold} />
        </div>
      </CardContent>
    </Card>
  );
}
