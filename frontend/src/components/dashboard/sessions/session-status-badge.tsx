import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { SessionStatus } from "@/lib/api/types";
import {
  Loader2,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  PlayCircle,
  BrainCircuit,
  Eye,
} from "lucide-react";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold font-mono transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9]",
        secondary:
          "bg-[#111720] text-[#F5F7FA] border border-[#202833] hover:bg-[#111720]/80",
        destructive:
          "bg-[#F05252]/15 text-[#F05252] border border-[#F05252]/20 hover:bg-[#F05252]/25",
        outline:
          "text-[#F5F7FA] border border-[#202833] hover:bg-[#111720] hover:text-[#22D3EE]",
        success:
          "bg-[#2DD4A3]/15 text-[#2DD4A3] border border-[#2DD4A3]/20 hover:bg-[#2DD4A3]/25",
        warning:
          "bg-[#F5B942]/15 text-[#F5B942] border border-[#F5B942]/20 hover:bg-[#F5B942]/25",
        info: "bg-[#22D3EE]/15 text-[#22D3EE] border border-[#22D3EE]/20 hover:bg-[#22D3EE]/25",
        cyan: "bg-[#22D3EE]/15 text-[#22D3EE] border border-[#22D3EE]/20 hover:bg-[#22D3EE]/25",
        gray: "bg-[#111720] text-[#9CA6B5] border border-[#202833] hover:bg-[#111720]/80",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export function SessionStatusBadge({
  status,
  className,
}: {
  status: SessionStatus;
  className?: string;
}) {
  let variant: BadgeProps["variant"] = "default";
  let Icon = Loader2;
  let animate = false;

  switch (status) {
    case SessionStatus.Pending:
      variant = "gray";
      Icon = Clock;
      break;
    case SessionStatus.Planning:
      variant = "cyan";
      Icon = BrainCircuit;
      animate = true;
      break;
    case SessionStatus.Executing:
      variant = "info";
      Icon = PlayCircle;
      animate = true;
      break;
    case SessionStatus.WaitingApproval:
      variant = "warning";
      Icon = AlertCircle;
      animate = true;
      break;
    case SessionStatus.Reflecting:
      variant = "cyan";
      Icon = Eye;
      animate = true;
      break;
    case SessionStatus.Evaluating:
      variant = "secondary";
      Icon = Loader2;
      animate = true;
      break;
    case SessionStatus.Completed:
      variant = "success";
      Icon = CheckCircle2;
      break;
    case SessionStatus.Failed:
      variant = "destructive";
      Icon = XCircle;
      break;
    case SessionStatus.Cancelled:
      variant = "gray";
      Icon = XCircle;
      break;
  }

  // Convert status to Title Case
  const label = status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

  return (
    <Badge
      variant={variant}
      className={cn("gap-1.5 whitespace-nowrap", className)}
    >
      <Icon className={cn("h-3.5 w-3.5", animate && "animate-pulse")} />
      {label}
    </Badge>
  );
}
