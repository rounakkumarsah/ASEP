"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { 
  Loader2, 
  Folder, 
  Plus, 
  Search, 
  Trash2, 
  Play, 
  AlertTriangle,
  Clock,
  CheckCircle2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { motion, AnimatePresence } from "framer-motion";

interface AgentRun {
  id: string;
  goal: string;
  plan: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

export default function ProjectsPage() {
  const [runs, setRuns] = React.useState<AgentRun[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [search, setSearch] = React.useState("");
  
  // Create project fields
  const [showCreate, setShowCreate] = React.useState(false);
  const [newGoal, setNewGoal] = React.useState("");
  const [newPlan, setNewPlan] = React.useState("");
  const [creating, setCreating] = React.useState(false);

  const fetchRuns = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiClient.get("/api/v1/agent-runs/");
      // The API returns PaginatedResponse[AgentRunResponse]
      const items = res.data.items || [];
      setRuns(items);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to load agent runs from server.");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchRuns();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGoal) return;
    setCreating(true);
    setError("");
    try {
      const planArray = newPlan ? newPlan.split("\n").filter(line => line.trim()) : ["Initialize workspace", "Scan code architecture", "Produce solution plan"];
      const res = await apiClient.post("/api/v1/agent-runs/", {
        goal: newGoal,
        plan: planArray
      });
      setRuns(prev => [res.data, ...prev]);
      setNewGoal("");
      setNewPlan("");
      setShowCreate(false);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to create agent run.");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this agent run?")) return;
    try {
      // Delete client side & hit API if route exists
      setRuns(prev => prev.filter(r => r.id !== id));
      // Try calling endpoint
      await apiClient.delete(`/api/v1/agent-runs/${id}`).catch(() => {});
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to delete agent run.");
    }
  };

  const filteredRuns = runs.filter(run => 
    run.goal.toLowerCase().includes(search.toLowerCase()) ||
    run.id.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="h-[400px] w-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Loading projects & agent sessions...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Active Workspaces & Projects</h1>
          <p className="text-muted-foreground mt-1">
            Create and manage autonomous software engineering tasks under organization context.
          </p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="font-semibold gap-2">
          <Plus className="h-4 w-4" />
          <span>New Workspace Goal</span>
        </Button>
      </div>

      {error && (
        <div className="p-4 border border-destructive/20 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Slide down creation block */}
      <AnimatePresence>
        {showCreate && (
          <motion.form
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            onSubmit={handleCreate}
            className="overflow-hidden border border-border/60 bg-card/40 backdrop-blur-sm p-6 rounded-xl space-y-4"
          >
            <h3 className="text-lg font-bold">Launch Agentic Workspace</h3>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Goal Description</label>
              <Input
                value={newGoal}
                onChange={e => setNewGoal(e.target.value)}
                placeholder="e.g. Write a python script to pull weather telemetry and save to local Postgres pool."
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Solution Plan Instructions (One step per line)</label>
              <textarea
                value={newPlan}
                onChange={e => setNewPlan(e.target.value)}
                placeholder="e.g.&#10;Initialize databases&#10;Configure endpoint handlers&#10;Verify unit tests"
                className="w-full text-sm p-3 rounded-lg border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary min-h-[100px]"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button type="submit" disabled={creating} className="gap-2 font-semibold">
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                <span>Start Agent Run</span>
              </Button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Main filter container */}
      <div className="flex items-center gap-2 max-w-md">
        <Search className="h-4 w-4 text-muted-foreground ml-2 absolute" />
        <Input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search workspace goals..."
          className="pl-9"
        />
      </div>

      {filteredRuns.length === 0 ? (
        <Card className="border border-dashed p-12 text-center flex flex-col items-center justify-center">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
            <Folder className="h-6 w-6" />
          </div>
          <CardTitle className="text-xl font-bold">No Active Agent Workspaces</CardTitle>
          <CardDescription className="max-w-md mt-2 mb-6">
            There are no ongoing agent runs assigned to your organization yet. Define a workspace goal to deploy an agent.
          </CardDescription>
          <Button onClick={() => setShowCreate(true)} className="font-semibold">
            Define First Goal
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRuns.map(run => (
            <Card key={run.id} className="border border-border/40 hover:border-border/70 transition-all bg-card/25 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-mono text-muted-foreground">{run.id}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    run.status === "completed" ? "bg-green-500/10 text-green-500" :
                    run.status === "running" ? "bg-primary/10 text-primary animate-pulse" : "bg-muted text-muted-foreground"
                  }`}>
                    {run.status.toUpperCase()}
                  </span>
                </div>
                <CardTitle className="text-base font-bold line-clamp-2 pt-2">{run.goal}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {run.plan && run.plan.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-wider">Solution Steps</p>
                    <div className="text-xs text-muted-foreground space-y-1">
                      {run.plan.slice(0, 3).map((p, idx) => (
                        <div key={idx} className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-muted-foreground/60" />
                          <span className="truncate">{p}</span>
                        </div>
                      ))}
                      {run.plan.length > 3 && (
                        <p className="text-[10px] font-semibold text-primary">+{run.plan.length - 3} more steps</p>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="flex items-center justify-between gap-4 border-t border-border/20 pt-3 text-[10px] text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(run.created_at).toLocaleDateString()}
                  </span>
                  
                  <div className="flex gap-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => handleDelete(run.id)}
                      className="h-7 w-7 text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
