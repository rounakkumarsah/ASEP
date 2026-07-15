import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { SessionStatus } from "@/lib/api/types"
import { 
  Loader2, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  PlayCircle,
  BrainCircuit,
  Eye
} from "lucide-react"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground border border-input hover:bg-accent hover:text-accent-foreground",
        success: "bg-green-500/15 text-green-700 dark:text-green-400 hover:bg-green-500/25",
        warning: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-500/25",
        info: "bg-blue-500/15 text-blue-700 dark:text-blue-400 hover:bg-blue-500/25",
        purple: "bg-purple-500/15 text-purple-700 dark:text-purple-400 hover:bg-purple-500/25",
        gray: "bg-muted text-muted-foreground hover:bg-muted/80",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export function SessionStatusBadge({ status, className }: { status: SessionStatus; className?: string }) {
  let variant: BadgeProps["variant"] = "default"
  let Icon = Loader2
  let animate = false

  switch (status) {
    case SessionStatus.Pending:
      variant = "gray"
      Icon = Clock
      break
    case SessionStatus.Planning:
      variant = "purple"
      Icon = BrainCircuit
      animate = true
      break
    case SessionStatus.Executing:
      variant = "info"
      Icon = PlayCircle
      animate = true
      break
    case SessionStatus.WaitingApproval:
      variant = "warning"
      Icon = AlertCircle
      animate = true
      break
    case SessionStatus.Reflecting:
      variant = "purple"
      Icon = Eye
      animate = true
      break
    case SessionStatus.Evaluating:
      variant = "secondary"
      Icon = Loader2
      animate = true
      break
    case SessionStatus.Completed:
      variant = "success"
      Icon = CheckCircle2
      break
    case SessionStatus.Failed:
      variant = "destructive"
      Icon = XCircle
      break
    case SessionStatus.Cancelled:
      variant = "gray"
      Icon = XCircle
      break
  }

  // Convert status to Title Case
  const label = status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')

  return (
    <Badge variant={variant} className={cn("gap-1.5 whitespace-nowrap", className)}>
      <Icon className={cn("h-3.5 w-3.5", animate && "animate-pulse")} />
      {label}
    </Badge>
  )
}
