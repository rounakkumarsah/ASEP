"use client";

import * as React from "react";
import { useKnowledge } from "@/lib/api/hooks/use-knowledge";
import { SearchToolbar } from "@/components/dashboard/shared/search-toolbar";
import { KnowledgeCard } from "@/components/dashboard/knowledge/knowledge-card";
import { Loader2, Database, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BentoGrid } from "@/components/ui/bento-grid";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { apiClient } from "@/lib/api/client";

export default function KnowledgeExplorerPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");

  // Upload modal state
  const [showUpload, setShowUpload] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [docTitle, setDocTitle] = React.useState("");
  const [docContent, setDocContent] = React.useState("");
  const [uploadError, setUploadError] = React.useState("");

  // Simple debounce
  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data, isLoading, isError, refetch } = useKnowledge(debouncedQuery);
  const documents = data?.items || [];

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docTitle || !docContent) return;
    setUploading(true);
    setUploadError("");
    try {
      await apiClient.post("/api/v1/knowledge", {
        title: docTitle,
        content: docContent,
      });
      setDocTitle("");
      setDocContent("");
      setShowUpload(false);
      refetch();
    } catch (err: unknown) {
      setUploadError((err as Error).message || "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">
            Search and manage indexed documentation, codebases, and foundational vector memory.
          </p>
        </div>
        <Button onClick={() => setShowUpload(!showUpload)} className="gap-2">
          <Upload className="h-4 w-4" />
          Upload Document
        </Button>
      </div>

      {showUpload && (
        <Card className="border-primary/30 bg-card/40">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Upload Knowledge Document</CardTitle>
            <CardDescription>Index documentation text into the Qdrant vector database for RAG context.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Document Title</label>
                <Input 
                  placeholder="e.g. Architecture RFC & API Contracts" 
                  value={docTitle} 
                  onChange={e => setDocTitle(e.target.value)} 
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Content Text</label>
                <textarea 
                  rows={5}
                  placeholder="Paste document markdown or text content..." 
                  value={docContent} 
                  onChange={e => setDocContent(e.target.value)} 
                  className="w-full p-3 text-sm rounded-md border border-input bg-background font-mono focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  required
                />
              </div>
              {uploadError && <p className="text-xs text-destructive">{uploadError}</p>}
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowUpload(false)}>Cancel</Button>
                <Button type="submit" disabled={uploading}>
                  {uploading ? "Indexing Document..." : "Index Document"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

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
              <p className="font-medium">
                Failed to retrieve knowledge documents
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                className="mt-4"
              >
                Retry Connection
              </Button>
            </div>
          ) : documents.length === 0 ? (
            <EmptyState
              icon={Database}
              title={searchQuery ? "No results found" : "Upload your first document"}
              description={
                searchQuery
                  ? `No results match your search query "${searchQuery}". Try adjusting your filters.`
                  : "The universal knowledge base parses and indexes document files for multi-agent RAG memory pools. Upload your first document to start."
              }
              action={
                !searchQuery && (
                  <Button className="font-semibold gap-2" onClick={() => setShowUpload(true)}>
                    <Upload className="h-4 w-4" />
                    Upload Document
                  </Button>
                )
              }
            />
          ) : (
            <BentoGrid className="pb-10">
              {documents.map((doc) => (
                <KnowledgeCard key={doc.id} document={doc} />
              ))}
            </BentoGrid>
          )}
        </div>
      </div>
    </div>
  );
}
