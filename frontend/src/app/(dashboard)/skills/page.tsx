"use client";

import * as React from "react";
import {
  Sparkles,
  Plus,
  Upload,
  Download,
  Copy,
  Trash2,
  Edit3,
  Check,
  FileCode,
  Paperclip,
  Play,
  RotateCcw,
  Search,
  CheckCircle2,
  Lock,
  Boxes,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import ReactMarkdown from "react-markdown";

interface SkillAttachment {
  filename: string;
  file_type: string;
  file_size: number;
  status: "ready" | "partially_parsed" | "failed";
  chunk_count: number;
  uploaded_at: string;
}

interface Skill {
  name: string;
  description: string;
  trigger: string;
  instructions: string;
  dependencies: string[];
  scope: "workspace" | "project";
  project_id?: string | null;
  enabled: boolean;
  is_builtin: boolean;
  version: number;
  attachments: SkillAttachment[];
  version_history: Array<{ version: number; instructions: string; saved_at: string }>;
  created_at: string;
  updated_at: string;
}

export default function SkillsPage() {
  const [skills, setSkills] = React.useState<Skill[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [scopeFilter, setScopeFilter] = React.useState<"all" | "builtin" | "user" | "workspace" | "project">("all");
  const [toastMessage, setToastMessage] = React.useState<string | null>(null);

  // Editor Modal state
  const [isEditorOpen, setIsEditorOpen] = React.useState(false);
  const [editingSkill, setEditingSkill] = React.useState<Skill | null>(null);
  const [editorTab, setEditorTab] = React.useState<"edit" | "preview" | "attachments">("edit");
  const [formName, setFormName] = React.useState("");
  const [formDesc, setFormDesc] = React.useState("");
  const [formTrigger, setFormTrigger] = React.useState("");
  const [formScope, setFormScope] = React.useState<"workspace" | "project">("workspace");
  const [formDeps, setFormDeps] = React.useState("");
  const [formInstructions, setFormInstructions] = React.useState("");
  const [formSaving, setFormSaving] = React.useState(false);

  // Attachment upload state
  const [uploadingFile, setUploadingFile] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const importInputRef = React.useRef<HTMLInputElement>(null);

  // Test Simulator Modal state
  const [isTestOpen, setIsTestOpen] = React.useState(false);
  const [testSkillName, setTestSkillName] = React.useState<string | null>(null);
  const [testGoal, setTestGoal] = React.useState("Build an authenticated REST endpoint with validation and tests");
  const [testLoading, setTestLoading] = React.useState(false);
  const [testResult, setTestResult] = React.useState<{
    active_skills: string[];
    retrieved_chunks: Array<{ citation: string; text: string }>;
    injected_system_prompt: string;
  } | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchSkills = React.useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/v1/skills");
      if (res.ok) {
        const data = await res.json();
        setSkills(data);
      }
    } catch (err) {
      console.error("Failed to load skills:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const handleToggle = async (skill: Skill, newEnabled: boolean) => {
    try {
      const res = await fetch(`/api/v1/skills/${skill.name}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: newEnabled }),
      });
      if (res.ok) {
        setSkills((prev) =>
          prev.map((s) => (s.name === skill.name ? { ...s, enabled: newEnabled } : s))
        );
        showToast(`Skill '${skill.name}' ${newEnabled ? "enabled" : "disabled"}`);
      }
    } catch (err) {
      console.error("Failed to toggle skill:", err);
    }
  };

  const handleDelete = async (skillName: string) => {
    if (!confirm(`Are you sure you want to delete user skill '${skillName}'?`)) return;
    try {
      const res = await fetch(`/api/v1/skills/${skillName}`, { method: "DELETE" });
      if (res.ok) {
        setSkills((prev) => prev.filter((s) => s.name !== skillName));
        showToast(`Skill '${skillName}' deleted`);
      } else {
        const err = await res.json();
        showToast(`Error: ${err.detail || "Failed to delete"}`);
      }
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleDuplicate = async (skillName: string) => {
    try {
      const res = await fetch(`/api/v1/skills/${skillName}/duplicate`, { method: "POST" });
      if (res.ok) {
        const dup = await res.json();
        setSkills((prev) => [dup, ...prev]);
        showToast(`Duplicated as '${dup.name}'`);
      }
    } catch (err) {
      console.error("Duplicate failed:", err);
    }
  };

  const handleExport = (skillName: string, format: "md" | "zip" = "md") => {
    window.open(`/api/v1/skills/${skillName}/export?format=${format}`, "_blank");
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/v1/skills/import", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const imported = await res.json();
        setSkills((prev) => [imported, ...prev]);
        showToast(`Imported skill '${imported.name}' successfully!`);
      } else {
        const err = await res.json();
        showToast(`Import failed: ${err.detail || "Invalid format"}`);
      }
    } catch (err) {
      console.error("Import failed:", err);
    } finally {
      if (importInputRef.current) importInputRef.current.value = "";
    }
  };

  const openCreateModal = () => {
    setEditingSkill(null);
    setFormName("");
    setFormDesc("");
    setFormTrigger("");
    setFormScope("workspace");
    setFormDeps("");
    setFormInstructions(
      "# Skill Directives\n\n## Objective\nDescribe what the agent should accomplish when this skill activates.\n\n## Rules\n1. Always validate inputs.\n2. Write strict types."
    );
    setEditorTab("edit");
    setIsEditorOpen(true);
  };

  const openEditModal = (skill: Skill) => {
    setEditingSkill(skill);
    setFormName(skill.name);
    setFormDesc(skill.description);
    setFormTrigger(skill.trigger);
    setFormScope(skill.scope);
    setFormDeps(skill.dependencies.join(", "));
    setFormInstructions(skill.instructions);
    setEditorTab("edit");
    setIsEditorOpen(true);
  };

  const handleSaveSkill = async () => {
    if (!formName.trim()) {
      showToast("Skill name is required");
      return;
    }

    setFormSaving(true);
    try {
      if (editingSkill) {
        // Update
        const res = await fetch(`/api/v1/skills/${editingSkill.name}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            description: formDesc,
            trigger: formTrigger,
            scope: formScope,
            dependencies: formDeps.split(",").map((s) => s.trim()).filter(Boolean),
            instructions: formInstructions,
          }),
        });
        if (res.ok) {
          const updated = await res.json();
          setSkills((prev) => prev.map((s) => (s.name === updated.name ? updated : s)));
          setEditingSkill(updated);
          showToast("Skill updated successfully!");
          setIsEditorOpen(false);
        } else {
          const err = await res.json();
          showToast(`Error: ${err.detail || "Failed to update"}`);
        }
      } else {
        // Create
        const res = await fetch("/api/v1/skills", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: formName,
            description: formDesc,
            trigger: formTrigger,
            scope: formScope,
            dependencies: formDeps.split(",").map((s) => s.trim()).filter(Boolean),
            instructions: formInstructions,
          }),
        });
        if (res.ok) {
          const created = await res.json();
          setSkills((prev) => [created, ...prev]);
          showToast(`Created skill '${created.name}'!`);
          setIsEditorOpen(false);
        } else {
          const err = await res.json();
          showToast(`Error: ${err.detail || "Failed to create"}`);
        }
      }
    } catch (err) {
      console.error("Save failed:", err);
    } finally {
      setFormSaving(false);
    }
  };

  const handleUploadAttachment = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!editingSkill) return;
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingFile(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`/api/v1/skills/${editingSkill.name}/attachments`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const att = await res.json();
        const updated = {
          ...editingSkill,
          attachments: [...editingSkill.attachments.filter((a) => a.filename !== att.filename), att],
        };
        setEditingSkill(updated);
        setSkills((prev) => prev.map((s) => (s.name === updated.name ? updated : s)));
        showToast(`Uploaded '${att.filename}' (${att.chunk_count} chunks indexed)`);
      } else {
        const err = await res.json();
        showToast(`Upload failed: ${err.detail || "Error"}`);
      }
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteAttachment = async (filename: string) => {
    if (!editingSkill) return;
    try {
      const res = await fetch(`/api/v1/skills/${editingSkill.name}/attachments/${filename}`, {
        method: "DELETE",
      });
      if (res.ok) {
        const updated = {
          ...editingSkill,
          attachments: editingSkill.attachments.filter((a) => a.filename !== filename),
        };
        setEditingSkill(updated);
        setSkills((prev) => prev.map((s) => (s.name === updated.name ? updated : s)));
        showToast(`Deleted attachment '${filename}'`);
      }
    } catch (err) {
      console.error("Delete attachment failed:", err);
    }
  };

  const handleRestoreVersion = async (versionIdx: number) => {
    if (!editingSkill) return;
    try {
      const res = await fetch(`/api/v1/skills/${editingSkill.name}/restore-version`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version_idx: versionIdx }),
      });
      if (res.ok) {
        const restored = await res.json();
        setEditingSkill(restored);
        setFormInstructions(restored.instructions);
        setSkills((prev) => prev.map((s) => (s.name === restored.name ? restored : s)));
        showToast("Version restored successfully!");
      }
    } catch (err) {
      console.error("Restore failed:", err);
    }
  };

  const openTestModal = (skillName: string) => {
    setTestSkillName(skillName);
    setTestResult(null);
    setIsTestOpen(true);
  };

  const runTestSimulation = async () => {
    if (!testSkillName) return;
    setTestLoading(true);
    try {
      const res = await fetch(`/api/v1/skills/${testSkillName}/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sample_goal: testGoal }),
      });
      if (res.ok) {
        const data = await res.json();
        setTestResult(data);
      } else {
        showToast("Test simulation failed");
      }
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setTestLoading(false);
    }
  };

  const filteredSkills = skills.filter((skill) => {
    if (scopeFilter === "builtin" && !skill.is_builtin) return false;
    if (scopeFilter === "user" && skill.is_builtin) return false;
    if (scopeFilter === "workspace" && skill.scope !== "workspace") return false;
    if (scopeFilter === "project" && skill.scope !== "project") return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const inName = skill.name.toLowerCase().includes(q);
      const inDesc = skill.description.toLowerCase().includes(q);
      const inTrig = skill.trigger.toLowerCase().includes(q);
      if (!inName && !inDesc && !inTrig) return false;
    }
    return true;
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#0A0D12] text-zinc-100">
      {/* Toast banner */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-4 py-2.5 rounded-xl text-xs font-mono backdrop-blur-md shadow-2xl flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Hidden file input for import */}
      <input
        ref={importInputRef}
        type="file"
        accept=".md,.zip"
        className="hidden"
        onChange={handleImportFile}
      />

      {/* Header bar */}
      <div className="p-6 border-b border-border/40 bg-background/50 backdrop-blur-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
                Agent Skills
                <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30 text-[11px] font-mono">
                  Claude Format
                </Badge>
              </h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                Extend agent capabilities with trigger-based skills, reference document embeddings, and prompt injections.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => importInputRef.current?.click()}
            className="text-xs border-border/60 gap-1.5 h-9"
          >
            <Upload className="h-3.5 w-3.5" /> Import (.md / .zip)
          </Button>
          <Button
            size="sm"
            onClick={openCreateModal}
            className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs gap-1.5 h-9 font-medium shadow-lg shadow-cyan-950/40"
          >
            <Plus className="h-4 w-4" /> New Skill
          </Button>
        </div>
      </div>

      {/* Filter and search toolbar */}
      <div className="px-6 py-3 border-b border-border/30 bg-muted/10 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          {(["all", "builtin", "user", "workspace", "project"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setScopeFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                scopeFilter === s
                  ? "bg-zinc-800 text-zinc-100 shadow-sm border border-border/60"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/20"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search skills by name, trigger..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            className="pl-9 h-8 text-xs bg-background/60"
          />
        </div>
      </div>

      {/* Skills Grid */}
      <ScrollArea className="flex-1 p-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-56 rounded-2xl border border-border/40 bg-muted/20 animate-pulse" />
            ))}
          </div>
        ) : filteredSkills.length === 0 ? (
          <div className="h-80 flex flex-col items-center justify-center text-center p-6 border border-dashed border-border/40 rounded-2xl">
            <Boxes className="h-10 w-10 text-muted-foreground mb-3 opacity-50" />
            <h3 className="font-semibold text-sm text-foreground">No skills found</h3>
            <p className="text-xs text-muted-foreground max-w-sm mt-1">
              No skills match your current search or filter criteria. Create a new user skill or adjust filters.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredSkills.map((skill) => (
              <div
                key={skill.name}
                className="group relative rounded-2xl border border-border/60 bg-gradient-to-b from-[#10141B] to-[#0A0D12] p-5 shadow-lg hover:border-cyan-500/40 hover:shadow-cyan-950/20 transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Top Badges & Toggle */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {skill.is_builtin ? (
                        <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30 text-[10px] gap-1 font-mono">
                          <Lock className="h-2.5 w-2.5" /> Built-in
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 text-[10px] font-mono">
                          User Skill
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-[10px] text-muted-foreground border-border/50 capitalize font-mono">
                        {skill.scope}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] text-muted-foreground border-border/50 font-mono">
                        v{skill.version}
                      </Badge>
                    </div>

                    <Switch
                      checked={skill.enabled}
                      onCheckedChange={(checked: boolean) => handleToggle(skill, checked)}
                      className="data-[state=checked]:bg-cyan-600"
                    />
                  </div>

                  {/* Name and Description */}
                  <h3 className="font-semibold text-sm text-foreground group-hover:text-cyan-300 transition-colors flex items-center gap-1.5">
                    {skill.name}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2 leading-relaxed">
                    {skill.description || "Custom skill directives for autonomous agent execution."}
                  </p>

                  {/* Trigger keywords */}
                  {skill.trigger && (
                    <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] text-zinc-500 font-mono">Trigger:</span>
                      {skill.trigger.split(/[\s,]+/).slice(0, 4).map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-mono bg-zinc-900/90 text-zinc-300 px-1.5 py-0.5 rounded border border-border/50"
                        >
                          {t}
                        </span>
                      ))}
                      {skill.trigger.split(/[\s,]+/).length > 4 && (
                        <span className="text-[10px] text-zinc-500">+{skill.trigger.split(/[\s,]+/).length - 4}</span>
                      )}
                    </div>
                  )}

                  {/* Composed dependencies */}
                  {skill.dependencies && skill.dependencies.length > 0 && (
                    <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                      <span className="text-[10px] text-zinc-500 font-mono">Also applies:</span>
                      {skill.dependencies.map((dep) => (
                        <span
                          key={dep}
                          className="text-[10px] font-mono bg-purple-500/10 text-purple-400 px-1.5 py-0.5 rounded border border-purple-500/20"
                        >
                          {dep}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Attachment count */}
                  {skill.attachments && skill.attachments.length > 0 && (
                    <div className="mt-2.5 flex items-center gap-1 text-[11px] text-cyan-400 font-mono">
                      <Paperclip className="h-3 w-3" />
                      <span>{skill.attachments.length} reference file(s) indexed</span>
                    </div>
                  )}
                </div>

                {/* Footer Action Bar */}
                <div className="mt-5 pt-3.5 border-t border-border/40 flex items-center justify-between gap-1.5 text-xs">
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openTestModal(skill.name)}
                      className="h-7 px-2 text-xs text-zinc-300 hover:text-cyan-300 hover:bg-cyan-500/10 gap-1"
                      title="Test simulation"
                    >
                      <Play className="h-3 w-3 text-cyan-400" /> Test
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleExport(skill.name, skill.attachments?.length ? "zip" : "md")}
                      className="h-7 px-2 text-xs text-zinc-400 hover:text-zinc-200"
                      title="Export skill"
                    >
                      <Download className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDuplicate(skill.name)}
                      className="h-7 px-2 text-xs text-zinc-400 hover:text-zinc-200"
                      title="Duplicate skill"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>

                  <div className="flex items-center gap-1">
                    {!skill.is_builtin ? (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditModal(skill)}
                          className="h-7 px-2 text-xs text-zinc-300 hover:text-white"
                          title="Edit skill"
                        >
                          <Edit3 className="h-3 w-3" /> Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(skill.name)}
                          className="h-7 px-2 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                          title="Delete skill"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </>
                    ) : (
                      <span className="text-[10px] text-zinc-500 italic pr-1">Read-only built-in</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* CREATE / EDIT MODAL */}
      {isEditorOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background border border-border/80 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-border/40 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-foreground">
                    {editingSkill ? `Edit Skill: ${editingSkill.name}` : "Create New Skill"}
                  </h3>
                  <p className="text-[11px] text-muted-foreground">YAML frontmatter + Markdown Claude Agent Skill specification</p>
                </div>
              </div>
              <button
                onClick={() => setIsEditorOpen(false)}
                className="text-muted-foreground hover:text-foreground text-sm px-2 py-1"
              >
                ✕
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex border-b border-border/40 px-5 text-xs bg-muted/20">
              <button
                type="button"
                onClick={() => setEditorTab("edit")}
                className={`py-2.5 px-4 font-medium border-b-2 transition-all ${
                  editorTab === "edit"
                    ? "border-cyan-400 text-cyan-300"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                Editor
              </button>
              <button
                type="button"
                onClick={() => setEditorTab("preview")}
                className={`py-2.5 px-4 font-medium border-b-2 transition-all ${
                  editorTab === "preview"
                    ? "border-cyan-400 text-cyan-300"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                Markdown Preview
              </button>
              {editingSkill && (
                <button
                  type="button"
                  onClick={() => setEditorTab("attachments")}
                  className={`py-2.5 px-4 font-medium border-b-2 transition-all flex items-center gap-1.5 ${
                    editorTab === "attachments"
                      ? "border-cyan-400 text-cyan-300"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Paperclip className="h-3 w-3" /> Reference Files ({editingSkill.attachments?.length || 0})
                </button>
              )}
            </div>

            {/* Modal Body */}
            <ScrollArea className="flex-1 p-6">
              {editorTab === "edit" ? (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="font-semibold text-muted-foreground">Skill Name (Slug)</label>
                      <Input
                        placeholder="e.g. django-rest-expert"
                        value={formName}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormName(e.target.value)}
                        disabled={!!editingSkill}
                        className="mt-1 font-mono text-xs"
                      />
                    </div>
                    <div>
                      <label className="font-semibold text-muted-foreground">Scope</label>
                      <select
                        value={formScope}
                        onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFormScope(e.target.value as "workspace" | "project")}
                        className="w-full text-xs p-2 rounded-md border border-input bg-background mt-1"
                      >
                        <option value="workspace">Workspace-level (Available in all projects)</option>
                        <option value="project">Project-level (Current project only)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="font-semibold text-muted-foreground">Description</label>
                    <Input
                      placeholder="e.g. Expert in building idiomatic Django REST Framework APIs"
                      value={formDesc}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormDesc(e.target.value)}
                      className="mt-1 text-xs"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-muted-foreground">
                      Trigger Keywords (Space or comma-separated)
                    </label>
                    <Input
                      placeholder="e.g. python django backend api drf rest"
                      value={formTrigger}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormTrigger(e.target.value)}
                      className="mt-1 font-mono text-xs"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-muted-foreground">
                      Composed Dependencies (Other skills to also apply)
                    </label>
                    <Input
                      placeholder="e.g. test-writer, security-auditor"
                      value={formDeps}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormDeps(e.target.value)}
                      className="mt-1 font-mono text-xs"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-muted-foreground">Markdown Instructions</label>
                    <textarea
                      value={formInstructions}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormInstructions(e.target.value)}
                      rows={10}
                      className="w-full p-3 font-mono text-xs rounded-xl border border-border bg-background mt-1 resize-y leading-relaxed text-zinc-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                      placeholder="Write instructions in markdown..."
                    />
                  </div>
                </div>
              ) : editorTab === "preview" ? (
                <div className="prose prose-invert prose-xs max-w-none p-4 rounded-xl border border-border/40 bg-zinc-950/60 font-sans">
                  <ReactMarkdown>{formInstructions}</ReactMarkdown>
                </div>
              ) : (
                /* Attachments Tab */
                <div className="space-y-4 text-xs">
                  <div className="border-2 border-dashed border-border/60 rounded-xl p-6 text-center hover:border-cyan-500/50 transition-colors bg-muted/10">
                    <Paperclip className="h-8 w-8 mx-auto mb-2 text-cyan-400 opacity-60" />
                    <h4 className="font-semibold text-sm text-foreground">Attach Reference Documents</h4>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Upload PDF, DOCX, TXT, MD, or code files (max 20 files / 50MB). Content is chunked (500 tokens) and embedded under namespace <code className="font-mono text-cyan-400">skill/{editingSkill?.name}</code>.
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.docx,.txt,.md,.py,.ts,.js,.json,.yaml,.yml,.sh,.sql"
                      className="hidden"
                      onChange={handleUploadAttachment}
                    />
                    <Button
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingFile}
                      className="mt-3 bg-cyan-600 hover:bg-cyan-500 text-white text-xs gap-1.5"
                    >
                      {uploadingFile ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
                      {uploadingFile ? "Processing & Chunking..." : "Choose File to Upload"}
                    </Button>
                  </div>

                  {/* File List */}
                  {editingSkill?.attachments && editingSkill.attachments.length > 0 && (
                    <div className="border border-border/50 rounded-xl overflow-hidden bg-background">
                      <div className="bg-muted/40 px-4 py-2 border-b border-border/40 flex justify-between items-center text-[11px] font-semibold text-muted-foreground">
                        <span>Indexed Reference Files</span>
                        <span>{editingSkill.attachments.length} / 20 files</span>
                      </div>
                      <div className="divide-y divide-border/40">
                        {editingSkill.attachments.map((att) => (
                          <div key={att.filename} className="px-4 py-3 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2.5">
                              <FileCode className="h-4 w-4 text-cyan-400" />
                              <div>
                                <span className="font-mono font-medium text-foreground">{att.filename}</span>
                                <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5 font-mono">
                                  <span>{(att.file_size / 1024).toFixed(1)} KB</span>
                                  <span>•</span>
                                  <span>{att.chunk_count} chunks</span>
                                  <span>•</span>
                                  <Badge
                                    variant="outline"
                                    className={`text-[9px] px-1 py-0 ${
                                      att.status === "ready"
                                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                    }`}
                                  >
                                    {att.status}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteAttachment(att.filename)}
                              className="h-7 w-7 p-0 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Version History */}
                  {editingSkill?.version_history && editingSkill.version_history.length > 0 && (
                    <div className="p-3 rounded-xl border border-border/40 bg-muted/20 space-y-2">
                      <h5 className="font-semibold text-xs text-foreground flex items-center gap-1.5">
                        <RotateCcw className="h-3.5 w-3.5 text-cyan-400" /> Version History (Last 3)
                      </h5>
                      {editingSkill.version_history.map((vh, idx) => (
                        <div key={idx} className="flex items-center justify-between text-[11px] p-2 rounded-lg bg-background border border-border/40 font-mono">
                          <div>
                            <span className="font-semibold text-cyan-300">v{vh.version}</span>
                            <span className="text-zinc-500 ml-2">{new Date(vh.saved_at).toLocaleTimeString()}</span>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRestoreVersion(idx)}
                            className="h-6 text-[10px] px-2"
                          >
                            Restore
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </ScrollArea>

            {/* Modal Footer */}
            <div className="p-4 border-t border-border/40 flex items-center justify-end gap-2 bg-muted/10">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditorOpen(false)}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSaveSkill}
                disabled={formSaving}
                className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs gap-1.5"
              >
                {formSaving ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                {editingSkill ? "Save Changes" : "Create Skill"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* TEST SIMULATOR MODAL */}
      {isTestOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background border border-border/80 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-border/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Play className="h-4 w-4 text-cyan-400" />
                <h3 className="font-semibold text-sm text-foreground">
                  Test Skill Injection: <span className="font-mono text-cyan-300">{testSkillName}</span>
                </h3>
              </div>
              <button onClick={() => setIsTestOpen(false)} className="text-muted-foreground hover:text-foreground text-sm">
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs flex-1 overflow-y-auto">
              <div>
                <label className="font-semibold text-muted-foreground">Sample User Goal / Request</label>
                <div className="flex gap-2 mt-1">
                  <Input
                    value={testGoal}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTestGoal(e.target.value)}
                    className="text-xs"
                    placeholder="Describe a sample task..."
                  />
                  <Button
                    size="sm"
                    onClick={runTestSimulation}
                    disabled={testLoading}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs shrink-0 gap-1.5"
                  >
                    {testLoading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                    Simulate
                  </Button>
                </div>
              </div>

              {testResult && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-muted-foreground">Active Skills Resolved:</span>
                    {testResult.active_skills.map((s) => (
                      <Badge key={s} variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30 text-[10px] font-mono">
                        [SKILL: {s}]
                      </Badge>
                    ))}
                  </div>

                  {testResult.retrieved_chunks && testResult.retrieved_chunks.length > 0 && (
                    <div>
                      <span className="font-semibold text-muted-foreground">Top Retrieved Attachment Citations:</span>
                      <div className="mt-1 space-y-1">
                        {testResult.retrieved_chunks.map((c, i) => (
                          <div key={i} className="p-2 rounded-lg bg-zinc-900 border border-border/40 font-mono text-[11px] text-emerald-300">
                            {c.citation}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <span className="font-semibold text-muted-foreground">Resulting System Prompt Injection:</span>
                    <pre className="p-3.5 rounded-xl bg-zinc-950 border border-border/50 text-[11px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-60 mt-1">
                      {testResult.injected_system_prompt}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
