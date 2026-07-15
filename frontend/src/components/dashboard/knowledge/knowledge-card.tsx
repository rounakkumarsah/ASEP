import * as React from "react"
import { KnowledgeDocument } from "@/lib/api/types"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { FileText, Database } from "lucide-react"

export function KnowledgeCard({ document }: { document: KnowledgeDocument }) {
  const date = new Date(document.createdAt).toLocaleDateString(undefined, { 
    month: "short", day: "numeric", year: "numeric"
  })

  return (
    <Card className="hover:border-primary/50 transition-colors h-full flex flex-col group cursor-pointer">
      <CardHeader className="p-4 pb-2 border-b border-border/40 space-y-1">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 text-primary">
            <FileText className="h-4 w-4" />
            <h3 className="font-semibold text-sm leading-none group-hover:underline decoration-primary/50 underline-offset-4">
              {document.title}
            </h3>
          </div>
        </div>
        <div className="flex items-center text-xs text-muted-foreground gap-3">
          <span className="flex items-center gap-1">
            <Database className="h-3 w-3" />
            {document.source}
          </span>
          <span>Added {date}</span>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-3 flex-1 flex flex-col">
        <p className="text-sm text-muted-foreground leading-relaxed flex-1 line-clamp-3">
          {document.snippet}
        </p>
        
        <div className="mt-4 flex gap-1.5 flex-wrap">
          {document.tags.map(tag => (
            <span key={tag} className="inline-flex items-center rounded-md bg-secondary/50 px-2 py-0.5 text-[10px] font-medium text-secondary-foreground border border-border/50">
              #{tag}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
