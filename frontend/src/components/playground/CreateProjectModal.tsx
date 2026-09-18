"use client";

import * as React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FolderPlus, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";

interface CreateProjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated?: (project: { id: string; name: string }) => void;
}

export function CreateProjectModal({
  open,
  onOpenChange,
  onProjectCreated,
}: CreateProjectModalProps) {
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [error, setError] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const { setProject } = usePlaygroundStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanName = name.trim();
    if (!cleanName) {
      setError("Project name is required.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    const fallbackProject = {
      id: `prj_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      name: cleanName,
    };

    try {
      const res = await apiClient.post("/api/v1/projects", {
        name: cleanName,
        description: description.trim() || undefined,
      });

      const created = {
        id: res.data?.id || fallbackProject.id,
        name: res.data?.name || fallbackProject.name,
      };

      setProject(created.id, created.name);
      setName("");
      setDescription("");
      onOpenChange(false);
      if (onProjectCreated) {
        onProjectCreated(created);
      }
    } catch {
      // Fallback for demo/guest sessions or offline
      setProject(fallbackProject.id, fallbackProject.name);
      setName("");
      setDescription("");
      onOpenChange(false);
      if (onProjectCreated) {
        onProjectCreated(fallbackProject);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px] bg-[#0D1117] border border-[#202833] text-foreground p-6 shadow-2xl">
        <DialogHeader className="space-y-2">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <FolderPlus className="h-5 w-5" />
            </div>
            <DialogTitle className="text-lg font-bold text-[#F5F7FA]">Create New Project</DialogTitle>
          </div>
          <DialogDescription className="text-xs text-muted-foreground">
            Projects group conversations, repository code, diffs, and security scans together.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label htmlFor="proj-name" className="text-xs font-medium text-[#F5F7FA]">
              Project Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="proj-name"
              placeholder="e.g. Next.js SaaS, Python API, Mobile Backend"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (error) setError("");
              }}
              className="bg-[#111720] border-[#202833] text-sm focus-visible:ring-primary h-9"
              autoFocus
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="proj-desc" className="text-xs font-medium text-[#F5F7FA]">
              Description <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Input
              id="proj-desc"
              placeholder="What is this project building or testing?"
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
              className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold gap-1.5 shadow-md"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Create Project
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
