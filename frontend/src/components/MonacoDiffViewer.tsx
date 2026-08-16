"use client";

import React, { useState } from "react";
import { DiffEditor } from "@monaco-editor/react";
import { Button } from "@/components/ui/button";

interface DiffFile {
  path: string;
  original: string;
  modified: string;
  language?: string;
}

interface MonacoDiffViewerProps {
  files: DiffFile[];
  onApprove: (path: string) => void;
  onReject: (path: string) => void;
  readOnly?: boolean;
}

const getLanguageFromPath = (path: string): string => {
  const ext = path.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "js":
    case "jsx":
      return "javascript";
    case "ts":
    case "tsx":
      return "typescript";
    case "py":
      return "python";
    case "json":
      return "json";
    case "md":
      return "markdown";
    case "html":
      return "html";
    case "css":
      return "css";
    case "sh":
    case "bash":
      return "shell";
    case "yml":
    case "yaml":
      return "yaml";
    default:
      return "plaintext";
  }
};

export const MonacoDiffViewer: React.FC<MonacoDiffViewerProps> = ({
  files,
  onApprove,
  onReject,
  readOnly = false,
}) => {
  const [activeFileIndex, setActiveFileIndex] = useState(0);

  if (!files || files.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-muted-foreground border border-dashed rounded-lg">
        No files to display diff comparison.
      </div>
    );
  }

  const activeFile = files[activeFileIndex];
  const language = activeFile.language || getLanguageFromPath(activeFile.path);

  return (
    <div className="flex flex-col h-full border border-border/50 rounded-lg bg-[#090B0F] overflow-hidden min-h-[500px]">
      {/* File Tab Bar */}
      <div className="flex bg-[#0D1117] border-b border-border/50 overflow-x-auto">
        {files.map((file, idx) => (
          <button
            key={file.path}
            onClick={() => setActiveFileIndex(idx)}
            className={`px-4 py-2 text-xs font-mono border-r border-border/50 transition-colors whitespace-nowrap ${
              idx === activeFileIndex
                ? "bg-[#090B0F] text-primary border-t-2 border-t-primary"
                : "text-muted-foreground hover:bg-[#111720] hover:text-foreground"
            }`}
          >
            {file.path.split("/").pop()}
          </button>
        ))}
      </div>

      {/* Editor Panel */}
      <div className="flex-1 w-full relative min-h-[400px]">
        <DiffEditor
          height="100%"
          language={language}
          original={activeFile.original}
          modified={activeFile.modified}
          theme="vs-dark"
          options={{
            readOnly: readOnly,
            originalEditable: false,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderSideBySide: true,
          }}
        />
      </div>

      {/* Footer Approvals Actions */}
      {!readOnly && (
        <div className="flex items-center justify-between px-6 py-4 bg-[#0D1117] border-t border-border/50">
          <span className="text-xs font-mono text-muted-foreground truncate max-w-sm md:max-w-md">
            Reviewing: <code className="text-foreground">{activeFile.path}</code>
          </span>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              className="border-destructive/30 text-destructive hover:bg-destructive/10"
              onClick={() => onReject(activeFile.path)}
            >
              Reject
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => onApprove(activeFile.path)}
            >
              Approve
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

