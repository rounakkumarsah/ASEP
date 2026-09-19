"use client";

import * as React from "react";
import { useKnowledge } from "@/lib/api/hooks/use-knowledge";
import { SearchToolbar } from "@/components/dashboard/shared/search-toolbar";
import { KnowledgeCard } from "@/components/dashboard/knowledge/knowledge-card";
import { 
  Loader2, 
  Database, 
  Upload, 
  FileText, 
  FileCode, 
  CheckCircle2, 
  X, 
  Sparkles, 
  FileSpreadsheet, 
  FileType,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { BentoGrid } from "@/components/ui/bento-grid";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import { knowledgeService } from "@/lib/api/services/knowledge";

const SUPPORTED_FORMATS = [
  { ext: "PDF", desc: ".pdf (PyMuPDF parser)", color: "text-red-400 border-red-500/30 bg-red-500/10" },
  { ext: "DOCX", desc: ".docx (Word Document)", color: "text-blue-400 border-blue-500/30 bg-blue-500/10" },
  { ext: "TXT / MD", desc: ".txt, .md (Markdown)", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  { ext: "CSV / DATA", desc: ".csv, .json (Tabular & structured)", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
];

export default function KnowledgeExplorerPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");

  // Upload modal state
  const [showUpload, setShowUpload] = React.useState(false);
  const [uploadMode, setUploadMode] = React.useState<"file" | "text">("file");
  const [uploading, setUploading] = React.useState(false);
  const [docTitle, setDocTitle] = React.useState("");
  const [docContent, setDocContent] = React.useState("");
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [dragActive, setDragActive] = React.useState(false);
  const [uploadError, setUploadError] = React.useState("");
  const [toastMessage, setToastMessage] = React.useState<string | null>(null);

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4500);
  };

  // Simple debounce
  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data, isLoading, isError, refetch } = useKnowledge(debouncedQuery);
  const documents = data?.items || [];

  const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

  const handleFileSelect = (file: File) => {
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setUploadError(`File '${file.name}' (${sizeMB} MB) exceeds the maximum allowed limit of 25 MB. Please select a file under 25 MB.`);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setUploadError("");
    if (!docTitle) {
      const cleanName = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      setDocTitle(cleanName);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploading(true);
    setUploadError("");

    try {
      if (uploadMode === "file") {
        if (!selectedFile) {
          setUploadError("Please select a file to upload.");
          setUploading(false);
          return;
        }
        if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
          setUploadError(`File size (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB) exceeds 25 MB limit.`);
          setUploading(false);
          return;
        }
        await knowledgeService.uploadDocument(selectedFile);
        showToast(`Document '${selectedFile.name}' parsed and indexed successfully!`);
        setSelectedFile(null);
        setDocTitle("");
      } else {
        if (!docTitle || !docContent) {
          setUploadError("Title and text content are required.");
          setUploading(false);
          return;
        }
        await knowledgeService.indexTextDocument(docTitle, docContent);
        showToast(`Text document '${docTitle}' indexed successfully into Knowledge Base!`);
        setDocTitle("");
        setDocContent("");
      }

      setShowUpload(false);
      refetch();
    } catch (err: unknown) {
      setUploadError((err as Error).message || "Failed to index document.");
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split(".").pop()?.toLowerCase();
    if (ext === "pdf") return <FileType className="h-8 w-8 text-red-400" />;
    if (ext === "docx" || ext === "doc") return <FileText className="h-8 w-8 text-blue-400" />;
    if (ext === "csv" || ext === "xlsx" || ext === "xls") return <FileSpreadsheet className="h-8 w-8 text-amber-400" />;
    if (ext === "json" || ext === "md" || ext === "txt") return <FileCode className="h-8 w-8 text-emerald-400" />;
    return <FileText className="h-8 w-8 text-primary" />;
  };

  return (
    <div className="space-y-6 flex flex-col h-full">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-emerald-950/90 text-emerald-300 border border-emerald-500/40 px-4 py-3 rounded-lg shadow-xl backdrop-blur font-mono text-xs animate-in slide-in-from-bottom-5">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">
            Search and manage indexed documentation, codebases, and foundational vector memory.
          </p>
        </div>
        <Button onClick={() => setShowUpload(!showUpload)} className="gap-2 font-medium">
          <Upload className="h-4 w-4" />
          Upload Document
        </Button>
      </div>

      {showUpload && (
        <Card className="border-primary/30 bg-card/60 backdrop-blur shadow-xl transition-all">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Upload & Index Knowledge Document
                </CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Parse document files (PDF, DOCX, TXT, CSV) or index markdown text into the vector database for RAG context.
                </CardDescription>
              </div>
              
              {/* Upload Mode Selector */}
              <div className="flex items-center bg-muted/60 p-1 rounded-lg border border-border/50 text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setUploadMode("file")}
                  className={`px-3 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                    uploadMode === "file" 
                      ? "bg-primary text-primary-foreground shadow-xs font-semibold" 
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Upload className="h-3.5 w-3.5" />
                  Upload File
                </button>
                <button
                  type="button"
                  onClick={() => setUploadMode("text")}
                  className={`px-3 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                    uploadMode === "text" 
                      ? "bg-primary text-primary-foreground shadow-xs font-semibold" 
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <FileText className="h-3.5 w-3.5" />
                  Paste Text / MD
                </button>
              </div>
            </div>

            {/* Supported Formats Banner */}
            {uploadMode === "file" && (
              <div className="flex items-center gap-2 flex-wrap pt-2">
                <span className="text-[11px] text-muted-foreground font-mono uppercase tracking-wider">Supported:</span>
                {SUPPORTED_FORMATS.map((fmt) => (
                  <Badge key={fmt.ext} variant="outline" className={`text-[10px] font-mono px-2 py-0.5 border ${fmt.color}`}>
                    {fmt.ext}
                  </Badge>
                ))}
              </div>
            )}
          </CardHeader>

          <CardContent>
            <form onSubmit={handleUploadSubmit} className="space-y-4">
              {uploadMode === "file" ? (
                /* File Upload Zone */
                <div className="space-y-3">
                  {!selectedFile ? (
                    <div
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 ${
                        dragActive
                          ? "border-primary bg-primary/10 scale-[1.01]"
                          : "border-border/70 hover:border-primary/60 hover:bg-muted/20 bg-muted/5"
                      }`}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.docx,.doc,.txt,.md,.markdown,.csv,.json,.xlsx,.xls,.pptx"
                        onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                        className="hidden"
                      />
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                        <Upload className="h-6 w-6" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-foreground">
                          Drag and drop your document here, or <span className="text-primary underline">browse files</span>
                        </p>
                        <p className="text-xs text-muted-foreground font-mono">
                          Supports PDF, DOCX, TXT, Markdown, CSV, JSON (up to 25 MB)
                        </p>
                      </div>
                    </div>
                  ) : (
                    /* Selected File Preview Card */
                    <div className="p-4 rounded-xl border border-primary/30 bg-primary/5 flex items-center justify-between">
                      <div className="flex items-center gap-3 min-w-0">
                        {getFileIcon(selectedFile.name)}
                        <div className="min-w-0">
                          <p className="text-sm font-semibold truncate text-foreground">{selectedFile.name}</p>
                          <p className="text-xs text-muted-foreground font-mono">
                            {(selectedFile.size / 1024).toFixed(1)} KB • Ready to parse & index
                          </p>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => setSelectedFile(null)}
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="text-xs font-semibold uppercase text-muted-foreground">Document Title (optional override)</label>
                    <Input 
                      placeholder="e.g. Architecture RFC & API Contracts" 
                      value={docTitle} 
                      onChange={e => setDocTitle(e.target.value)} 
                    />
                  </div>
                </div>
              ) : (
                /* Manual Text/Markdown Entry */
                <div className="space-y-4">
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
                    <label className="text-xs font-semibold uppercase text-muted-foreground">Content Text / Markdown</label>
                    <textarea 
                      rows={6}
                      placeholder="Paste document markdown, technical specs, or text content..." 
                      value={docContent} 
                      onChange={e => setDocContent(e.target.value)} 
                      className="w-full p-3 text-sm rounded-md border border-input bg-background font-mono focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      required
                    />
                  </div>
                </div>
              )}

              {uploadError && (
                <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/10 p-2.5 rounded-md border border-destructive/20">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-border/40">
                <Button type="button" variant="ghost" onClick={() => setShowUpload(false)}>
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={uploading || (uploadMode === "file" && !selectedFile)}
                  className="gap-2 font-medium"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {uploadMode === "file" ? "Uploading & Parsing..." : "Indexing Document..."}
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      {uploadMode === "file" ? "Upload & Index Document" : "Index Document"}
                    </>
                  )}
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
