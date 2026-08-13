import * as React from "react";
import { KnowledgeDocument } from "@/lib/api/types";
import { BentoGridItem } from "@/components/ui/bento-grid";
import { FileText, Database } from "lucide-react";

export function KnowledgeCard({ document }: { document: KnowledgeDocument }) {
  const date = new Date(document.createdAt).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <BentoGridItem
      className="h-full border-border/40 hover:border-primary/50 cursor-pointer group"
      title={
        <div className="flex items-center gap-2 text-foreground group-hover:text-primary transition-colors">
          <FileText className="h-4 w-4" />
          <span className="font-semibold text-sm leading-none truncate">{document.title}</span>
        </div>
      }
      description={
        <div className="flex flex-col gap-3 mt-1">
          <p className="text-xs text-muted-foreground/80 line-clamp-3 leading-relaxed">
            {document.snippet}
          </p>
          <div className="flex gap-1.5 flex-wrap mt-auto pt-2">
            {document.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-md bg-secondary/50 px-2 py-0.5 text-[10px] font-medium text-secondary-foreground border border-border/50"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      }
      header={
        <div className="flex items-center justify-between text-[10px] text-muted-foreground uppercase tracking-wider font-semibold bg-muted/30 p-2 rounded-md mb-2">
          <span className="flex items-center gap-1.5">
            <Database className="h-3 w-3" />
            {document.source}
          </span>
          <span>{date}</span>
        </div>
      }
    />
  );
}
