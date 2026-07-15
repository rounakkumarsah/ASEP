"use client"

import * as React from "react"
import { useKnowledge } from "@/lib/api/hooks/use-knowledge"
import { SearchToolbar } from "@/components/dashboard/shared/search-toolbar"
import { KnowledgeCard } from "@/components/dashboard/knowledge/knowledge-card"
import { Loader2, Database } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function KnowledgeExplorerPage() {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [debouncedQuery, setDebouncedQuery] = React.useState("")

  // Simple debounce
  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const { data, isLoading, isError, refetch } = useKnowledge(debouncedQuery)
  const documents = data?.items || []

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">
            Search and manage indexed documentation, codebases, and foundational data.
          </p>
        </div>
        <Button>Upload Document</Button>
      </div>

      <SearchToolbar 
        placeholder="Search knowledge documents, collections, or tags..." 
        value={searchQuery}
        onChange={setSearchQuery}
      />

      <div className="flex flex-col flex-1 gap-6 pt-2">
        {/* Content Area */}
        <div className="flex-1 min-h-[400px]">
          {isLoading ? (
            <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
              <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
              <p>Searching knowledge indices...</p>
            </div>
          ) : isError ? (
            <div className="h-full w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg py-20">
              <p className="font-medium">Failed to retrieve knowledge documents</p>
              <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-4">
                Retry Connection
              </Button>
            </div>
          ) : documents.length === 0 ? (
            <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
              <div className="bg-muted h-12 w-12 rounded-full flex items-center justify-center mb-4">
                <Database className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="font-semibold text-foreground">No documents found</h3>
              <p className="text-sm mt-1 max-w-sm text-center">
                {searchQuery 
                  ? `No results match your search query.`
                  : `The knowledge base is currently empty.`}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pb-10">
              {documents.map(doc => (
                <KnowledgeCard key={doc.id} document={doc} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
