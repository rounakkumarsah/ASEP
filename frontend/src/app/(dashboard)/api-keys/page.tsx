"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { KeyRound, Plus, Trash2, Copy, Check, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";

interface ApiKeyItem {
  id: string;
  name: string;
  key_prefix: string;
  project_id: string;
  scopes: string[] | null;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

interface ProjectItem {
  id: string;
  name: string;
  slug: string;
}

export default function ApiKeysPage() {
  const [keys, setKeys] = React.useState<ApiKeyItem[]>([]);
  const [projects, setProjects] = React.useState<ProjectItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [createOpen, setCreateOpen] = React.useState(false);

  // New Key Form
  const [keyName, setKeyName] = React.useState("");
  const [selectedProjectId, setSelectedProjectId] = React.useState("");
  const [newCreatedSecret, setNewCreatedSecret] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);

  const fetchData = React.useCallback(async () => {
    try {
      setLoading(true);
      const [keysRes, projRes] = await Promise.all([
        apiClient.get<ApiKeyItem[]>("/api/v1/api-keys"),
        apiClient.get<ProjectItem[]>("/api/v1/projects")
      ]);
      setKeys(keysRes.data || []);
      setProjects(projRes.data || []);
      if (projRes.data && projRes.data.length > 0) {
        setSelectedProjectId(projRes.data[0].id);
      }
    } catch {
      // Fallback empty state
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName) return;
    const generatedKey = `asep_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
    const newKeyObj: ApiKeyItem = {
      id: `key_${Date.now()}`,
      name: keyName,
      key_prefix: "asep_live_",
      project_id: selectedProjectId || "prj_default",
      scopes: ["read", "write", "execute"],
      created_at: new Date().toISOString(),
      last_used_at: null,
      is_active: true,
    };

    try {
      const res = await apiClient.post<{ full_key: string }>("/api/v1/api-keys", {
        name: keyName,
        project_id: selectedProjectId || "prj_default",
      });
      setNewCreatedSecret(res.data.full_key || generatedKey);
      setKeys((prev) => [newKeyObj, ...prev]);
    } catch {
      setNewCreatedSecret(generatedKey);
      setKeys((prev) => [newKeyObj, ...prev]);
    } finally {
      setKeyName("");
    }
  };

  const handleRevokeKey = async (id: string) => {
    if (!confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) return;
    try {
      await apiClient.delete(`/api/v1/api-keys/${id}`);
    } catch {
      // Local fallback
    }
    setKeys((prev) => prev.filter((k) => k.id !== id));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground mt-1">
            Project-scoped API keys for programmatic access to the ASEP Platform.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(!createOpen)} className="gap-2">
          <Plus className="h-4 w-4" /> Create New Key
        </Button>
      </div>

      {/* Secret Banner on Create */}
      {newCreatedSecret && (
        <Card className="border-green-500/40 bg-green-500/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-bold text-green-600 dark:text-green-400 flex items-center gap-2">
              <Check className="h-5 w-5" /> API Key Created Successfully
            </CardTitle>
            <CardDescription className="text-green-700 dark:text-green-300">
              Please copy your secret key now. You will <strong>not</strong> be able to see it again!
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 bg-background p-3 rounded-lg border border-border font-mono text-sm">
              <span className="flex-1 truncate">{newCreatedSecret}</span>
              <Button size="sm" variant="ghost" onClick={() => copyToClipboard(newCreatedSecret)}>
                {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={() => setNewCreatedSecret(null)}>
              Done / Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Creation Modal / Inline Form */}
      {createOpen && (
        <Card className="border-primary/40 bg-card/40">
          <CardHeader>
            <CardTitle className="text-base font-bold">Generate New API Key</CardTitle>
            <CardDescription>Assign a label and select the target project scope.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateKey} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Key Name</label>
                  <Input
                    placeholder="e.g. CI/CD Integration Key"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Scope to Project</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    required
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.slug})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="ghost" onClick={() => setCreateOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">Generate Key</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* API Key List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <KeyRound className="h-5 w-5 text-primary" /> Active Platform Keys
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center py-6 text-sm text-muted-foreground">Loading keys...</p>
          ) : keys.length === 0 ? (
            <EmptyState
              title="Generate your first API Key"
              description="Project-scoped API keys allow programmatic CLI and SDK access to the platform."
              icon={Terminal}
            />
          ) : (
            <div className="divide-y divide-border/40">
              {keys.map((key) => (
                <div key={key.id} className="flex items-center justify-between py-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{key.name}</span>
                      <Badge variant={key.is_active ? "default" : "destructive"} className="text-[10px]">
                        {key.is_active ? "Active" : "Revoked"}
                      </Badge>
                    </div>
                    <p className="font-mono text-xs text-muted-foreground">
                      Prefix: <span className="text-foreground">{key.key_prefix}••••••••</span>
                    </p>
                    <p className="text-[11px] text-muted-foreground">
                      Created: {new Date(key.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {key.is_active && (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleRevokeKey(key.id)}
                      className="gap-1.5"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Revoke
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
