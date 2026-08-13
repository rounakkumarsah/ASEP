"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { 
  Loader2, 
  Folder, 
  Plus, 
  Search, 
  Trash2, 
  FolderPlus
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { AnimatedCard } from "@/components/ui/animated-card";

interface Project {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
}

export default function ProjectsPage() {
  const [projects, setProjects] = React.useState<Project[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [search, setSearch] = React.useState("");
  
  // Create project fields
  const [showCreate, setShowCreate] = React.useState(false);
  const [newName, setNewName] = React.useState("");
  const [newDesc, setNewDesc] = React.useState("");
  const [creating, setCreating] = React.useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiClient.get("/api/v1/projects");
      setProjects(res.data || []);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to load projects from server.");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName) return;
    setCreating(true);
    setError("");
    try {
      const res = await apiClient.post("/api/v1/projects", {
        name: newName,
        description: newDesc || undefined,
      });
      setProjects(prev => [res.data, ...prev]);
      setNewName("");
      setNewDesc("");
      setShowCreate(false);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(detail || (err as Error).message || "Failed to create project.");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this project?")) return;
    try {
      await apiClient.delete(`/api/v1/projects/${id}`);
      setProjects(prev => prev.filter(p => p.id !== id));
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to delete project.");
    }
  };

  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(search.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground py-24">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Loading projects...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 flex flex-col min-h-full pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground mt-1">
            Manage your autonomous software engineering workspaces.
          </p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Project
        </Button>
      </div>

      {error && (
        <div className="p-4 border border-destructive/30 bg-destructive/10 text-destructive text-sm rounded-lg">
          {error}
        </div>
      )}

      {showCreate && (
        <Card className="border-primary/30 bg-card/40">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">New Workspace Project</CardTitle>
            <CardDescription>Enter project details to scope multi-tenant API keys and AI agent runs.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Project Name</label>
                <Input 
                  placeholder="e.g. Next.js SaaS Microservice" 
                  value={newName} 
                  onChange={e => setNewName(e.target.value)} 
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Description (Optional)</label>
                <Input 
                  placeholder="e.g. Autonomous refactoring & test generation pipeline" 
                  value={newDesc} 
                  onChange={e => setNewDesc(e.target.value)} 
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button type="submit" disabled={creating}>
                  {creating ? "Creating..." : "Initialize Project"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {projects.length > 0 && (
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Search projects..." 
              value={search} 
              onChange={e => setSearch(e.target.value)}
              className="pl-9 bg-card/30"
            />
          </div>
        </div>
      )}

      {/* Projects Grid or Empty State */}
      {filteredProjects.length === 0 ? (
        <EmptyState
          icon={FolderPlus}
          title="Create your first project"
          description="Projects isolate agent runs, API key boundaries, and codebase telemetry."
          action={
            <Button onClick={() => setShowCreate(true)} className="gap-2 mt-2">
              <Plus className="h-4 w-4" />
              Create Project
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map(project => (
            <AnimatedCard key={project.id} className="flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Folder className="h-5 w-5 text-primary" />
                    <CardTitle className="text-base font-bold">{project.name}</CardTitle>
                  </div>
                  <Badge variant="outline" className="text-xs">Active</Badge>
                </div>
                <CardDescription className="text-xs line-clamp-2 mt-1">
                  {project.description || "Autonomous workspace project."}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0 flex items-center justify-between border-t border-border/30 mt-4 py-3 text-xs text-muted-foreground">
                <span className="font-mono">{project.slug}</span>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 text-destructive hover:bg-destructive/10 relative z-10"
                  onClick={() => handleDelete(project.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardContent>
            </AnimatedCard>
          ))}
        </div>
      )}
    </div>
  );
}
