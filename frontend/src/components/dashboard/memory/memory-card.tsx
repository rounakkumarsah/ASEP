import * as React from "react"
import { MemoryItem } from "@/lib/api/types"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Zap, BrainCircuit, Library, Briefcase, Activity } from "lucide-react"
import { cn } from "@/lib/utils"

function getMemoryConfig(type: MemoryItem["type"]) {
  switch (type) {
    case "working":
      return { icon: Zap, color: "text-blue-500", bg: "bg-blue-500/10", label: "Working Memory" }
    case "episodic":
      return { icon: Activity, color: "text-purple-500", bg: "bg-purple-500/10", label: "Episodic Memory" }
    case "semantic":
      return { icon: Library, color: "text-emerald-500", bg: "bg-emerald-500/10", label: "Semantic Memory" }
    case "procedural":
      return { icon: Briefcase, color: "text-amber-500", bg: "bg-amber-500/10", label: "Procedural Memory" }
    default:
      return { icon: BrainCircuit, color: "text-primary", bg: "bg-primary/10", label: "Unknown" }
  }
}

export function MemoryCard({ item }: { item: MemoryItem }) {
  const config = getMemoryConfig(item.type)
  const Icon = config.icon

  const date = new Date(item.createdAt).toLocaleDateString(undefined, { 
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" 
  })

  return (
    <Card className="hover:border-primary/50 transition-colors h-full flex flex-col">
      <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between border-b border-border/40">
        <div className="flex items-center gap-2">
          <div className={cn("p-1.5 rounded-md", config.bg)}>
            <Icon className={cn("h-4 w-4", config.color)} />
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {config.label}
          </span>
        </div>
        <span className="text-xs text-muted-foreground tabular-nums">{date}</span>
      </CardHeader>
      
      <CardContent className="p-4 pt-4 flex-1 flex flex-col">
        <p className="text-sm text-foreground leading-relaxed flex-1">
          {item.content}
        </p>
        
        <div className="mt-4 flex items-center justify-between">
          <div className="flex gap-1.5 flex-wrap">
            {item.tags.slice(0, 3).map(tag => (
              <span key={tag} className="inline-flex items-center rounded-md bg-secondary px-2 py-0.5 text-[10px] font-medium text-secondary-foreground">
                {tag}
              </span>
            ))}
            {item.tags.length > 3 && (
              <span className="inline-flex items-center rounded-md bg-secondary px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                +{item.tags.length - 3}
              </span>
            )}
          </div>
          
          {item.confidence && (
            <div className="flex flex-col items-end">
              <span className="text-[10px] text-muted-foreground uppercase">Confidence</span>
              <span className="text-xs font-medium tabular-nums">{Math.round(item.confidence * 100)}%</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
