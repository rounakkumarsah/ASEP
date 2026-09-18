"use client";

import * as React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Box, Sparkles } from "lucide-react";
import { useWorkspaceStore } from "@/lib/stores/workspaceStore";

interface CreateWorkspaceModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onWorkspaceCreated?: (workspaceId: string, workspaceName: string) => void;
}

export function CreateWorkspaceModal({
  open,
  onOpenChange,
  onWorkspaceCreated,
}: CreateWorkspaceModalProps) {
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [error, setError] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const { createWorkspace } = useWorkspaceStore();

  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Workspace name is required.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      const newWs = createWorkspace(name.trim(), description.trim());
      setName("");
      setDescription("");
      onOpenChange(false);
      if (onWorkspaceCreated) {
        onWorkspaceCreated(newWs.id, newWs.name);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create workspace.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px] bg-[#0D1117] border border-[#202833] text-foreground p-6 shadow-2xl">
        <DialogHeader className="space-y-2">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <Box className="h-5 w-5" />
            </div>
            <DialogTitle className="text-lg font-bold text-[#F5F7FA]">Create New Workspace</DialogTitle>
          </div>
          <DialogDescription className="text-xs text-muted-foreground">
            Workspaces organize agent runs, code repositories, knowledge files, and team access.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label htmlFor="ws-name" className="text-xs font-medium text-[#F5F7FA]">
              Workspace Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="ws-name"
              placeholder="e.g. Acme Corp, Mobile Team, Client Alpha"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (error) setError("");
              }}
              className="bg-[#111720] border-[#202833] text-sm focus-visible:ring-primary h-9"
              autoFocus
            />
            {slug && (
              <p className="text-[11px] text-muted-foreground font-mono">
                Slug: <span className="text-primary/90">asep.ai/ws/{slug}</span>
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="ws-desc" className="text-xs font-medium text-[#F5F7FA]">
              Description <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Input
              id="ws-desc"
              placeholder="Brief description of this workspace's purpose"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-[#111720] border-[#202833] text-sm focus-visible:ring-primary h-9"
            />
          </div>

          {error && <p className="text-xs text-destructive font-medium">{error}</p>}

          <DialogFooter className="pt-3 gap-2 sm:gap-0">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onOpenChange(false)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={!name.trim() || isSubmitting}
              className="bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold gap-1.5 shadow-md"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Create Workspace
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
