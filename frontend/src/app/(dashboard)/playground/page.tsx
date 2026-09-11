"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Terminal,
  RefreshCw,
  Bot,
  User as UserIcon,
  Plus,
  History,
  MessageSquare,
  Trash2,
  Folder,
  ChevronDown,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api/client";

/* --- Types --- */

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface PlaygroundSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
  model: string;
  projectId: string | null;
  projectName: string | null;
}

interface Project {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
}

/* --- Storage keys --- */

const STORAGE_MESSAGES_KEY = "asep_playground_messages";
const STORAGE_SESSIONS_KEY = "asep_playground_sessions";
const STORAGE_ACTIVE_ID_KEY = "asep_playground_active_id";

/* --- Helpers --- */

function ProjectBadge({ name, compact = false }: { name: string; compact?: boolean }) {
  return (
    <Link
      href="/projects"
      className={`inline-flex items-center gap-1 rounded-full border border-[#22D3EE]/30 bg-[#22D3EE]/10 text-[#22D3EE] hover:bg-[#22D3EE]/20 transition-colors ${
        compact ? "px-1.5 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs font-semibold"
      }`}
      title="View project"
    >
      <Folder className={compact ? "h-2.5 w-2.5" : "h-3 w-3"} />
      <span className="truncate max-w-[120px]">{name}</span>
      <ExternalLink className={compact ? "h-2 w-2 opacity-60" : "h-2.5 w-2.5 opacity-60"} />
    </Link>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="p-1 rounded hover:bg-white/10 transition-colors text-muted-foreground hover:text-foreground absolute top-2 right-2"
      title="Copy message"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

/* --- Page --- */

export default function PlaygroundPage() {
  const searchParams = useSearchParams();

  const [messages, setMessages] = React.useState<Message[]>([]);
  const [sessions, setSessions] = React.useState<PlaygroundSession[]>([]);
  const [activeSessionId, setActiveSessionId] = React.useState<string | null>(null);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [isLoaded, setIsLoaded] = React.useState(false);

  const [model, setModel] = React.useState("gemini-flash-latest");
  const [temperature, setTemperature] = React.useState("0.7");
  const [maxTokens, setMaxTokens] = React.useState("2048");

  const [projects, setProjects] = React.useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = React.useState<string | null>(null);
  const [selectedProjectName, setSelectedProjectName] = React.useState<string | null>(null);
  const [projectSelectorOpen, setProjectSelectorOpen] = React.useState(false);
  const projectSelectorRef = React.useRef<HTMLDivElement>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (projectSelectorRef.current && !projectSelectorRef.current.contains(e.target as Node)) {
        setProjectSelectorOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  React.useEffect(() => {
    apiClient.get("/api/v1/projects").then((res) => {
      if (res.data && Array.isArray(res.data)) setProjects(res.data);
    }).catch(() => {});
  }, []);

  React.useEffect(() => {
    if (typeof window === "undefined") return;

    const qProjectId = searchParams.get("projectId");
    const qProjectName = searchParams.get("projectName");
    if (qProjectId && qProjectName) {
      setSelectedProjectId(qProjectId);
      setSelectedProjectName(decodeURIComponent(qProjectName));
    }

    try {
      const storedSessions = localStorage.getItem(STORAGE_SESSIONS_KEY);
      const storedActiveId = localStorage.getItem(STORAGE_ACTIVE_ID_KEY);
      const storedMessages = localStorage.getItem(STORAGE_MESSAGES_KEY);

      let parsedSessions: PlaygroundSession[] = [];
      if (storedSessions) {
        parsedSessions = JSON.parse(storedSessions);
        setSessions(parsedSessions);
      }

      if (storedActiveId && parsedSessions.length > 0) {
        const active = parsedSessions.find((s) => s.id === storedActiveId);
        if (active && active.messages.length > 0) {
          setActiveSessionId(active.id);
          setMessages(active.messages);
          if (active.model) setModel(active.model);
          if (!qProjectId) {
            setSelectedProjectId(active.projectId ?? null);
            setSelectedProjectName(active.projectName ?? null);
          }
          setIsLoaded(true);
          return;
        }
      }

      if (storedMessages) {
        const msgs = JSON.parse(storedMessages);
        if (Array.isArray(msgs) && msgs.length > 0) {
          const fallbackSession: PlaygroundSession = {
            id: "session_" + Date.now(),
            title: msgs[0]?.content?.slice(0, 32) || "Chat Session",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            messages: msgs,
            model: "gemini-flash-latest",
            projectId: null,
            projectName: null,
          };
          setSessions([fallbackSession]);
          setActiveSessionId(fallbackSession.id);
          setMessages(msgs);
        }
      }
    } catch {
      // Storage parsing safeguard
    } finally {
      setIsLoaded(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const persistSession = React.useCallback(
    (newMessages: Message[], currentModel: string, currentSessionId: string | null, projId: string | null, projName: string | null) => {
      if (typeof window === "undefined" || !newMessages.length) return;
      try {
        localStorage.setItem(STORAGE_MESSAGES_KEY, JSON.stringify(newMessages));
        const title = newMessages[0]?.content?.slice(0, 36) || "Conversation";
        const now = new Date().toISOString();
        const sessionId = currentSessionId || `session_${Date.now()}`;
        setActiveSessionId(sessionId);
        localStorage.setItem(STORAGE_ACTIVE_ID_KEY, sessionId);
        setSessions((prev) => {
          const existingIdx = prev.findIndex((s) => s.id === sessionId);
          let updated: PlaygroundSession[];
          if (existingIdx >= 0) {
            updated = [...prev];
            updated[existingIdx] = {
              ...updated[existingIdx],
              title: updated[existingIdx].title || title,
              updatedAt: now,
              messages: newMessages,
              model: currentModel,
              projectId: projId,
              projectName: projName,
            };
          } else {
            updated = [{ id: sessionId, title, createdAt: now, updatedAt: now, messages: newMessages, model: currentModel, projectId: projId, projectName: projName }, ...prev];
          }
          localStorage.setItem(STORAGE_SESSIONS_KEY, JSON.stringify(updated));
          return updated;
        });
      } catch {
        // Storage quota safeguard
      }
    },
    []
  );

  const handleSelectSession = (session: PlaygroundSession) => {
    setActiveSessionId(session.id);
    setMessages(session.messages);
    if (session.model) setModel(session.model);
    setSelectedProjectId(session.projectId ?? null);
    setSelectedProjectName(session.projectName ?? null);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_ACTIVE_ID_KEY, session.id);
        localStorage.setItem(STORAGE_MESSAGES_KEY, JSON.stringify(session.messages));
      } catch {}
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setActiveSessionId(null);
    setSelectedProjectId(null);
    setSelectedProjectName(null);
    if (typeof window !== "undefined") {
      try {
        localStorage.removeItem(STORAGE_MESSAGES_KEY);
        localStorage.removeItem(STORAGE_ACTIVE_ID_KEY);
      } catch {}
    }
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== sessionId);
      if (typeof window !== "undefined") {
        try { localStorage.setItem(STORAGE_SESSIONS_KEY, JSON.stringify(next)); } catch {}
      }
      return next;
    });
    if (activeSessionId === sessionId) handleNewConversation();
  };

  const handleSelectProject = (project: Project | null) => {
    setSelectedProjectId(project ? project.id : null);
    setSelectedProjectName(project ? project.name : null);
    setProjectSelectorOpen(false);
  };

  const templates = [
    { name: "Code Review", prompt: "Perform a security code audit on this controller:" },
    { name: "SQL Optimization", prompt: "Rewrite this subquery into a high-performance JOIN sequence:" },
    { name: "Unit Test Writer", prompt: "Write comprehensive pytest functions for this FastAPI route:" },
  ];

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userText = input;
    const userMsg: Message = { role: "user", content: userText, timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    persistSession(nextMessages, model, activeSessionId, selectedProjectId, selectedProjectName);
    setInput("");
    setSending(true);
    try {
      const res = await apiClient.post("/api/v1/ai-runtime/chat/completions", {
        model,
        messages: nextMessages.map((m) => ({ role: m.role, content: m.content })),
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens, 10),
      }, { timeout: 90000 });
      const replyContent = res.data?.choices?.[0]?.message?.content || res.data?.content || "Model executed successfully.";
      const assistantMsg: Message = { role: "assistant", content: replyContent, timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) };
      const finalMessages = [...nextMessages, assistantMsg];
      setMessages(finalMessages);
      persistSession(finalMessages, model, activeSessionId, selectedProjectId, selectedProjectName);
    } catch (err: unknown) {
      const errDetail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      const assistantMsg: Message = { role: "assistant", content: `Error: ${errDetail || (err as Error).message || "Failed to execute AI completion request."}`, timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) };
      const finalMessages = [...nextMessages, assistantMsg];
      setMessages(finalMessages);
      persistSession(finalMessages, model, activeSessionId, selectedProjectId, selectedProjectName);
    } finally {
      setSending(false);
    }
  };

  const applyTemplate = (prompt: string) => setInput(prompt);

  /* --- Project Selector --- */
  const ProjectSelector = () => (
    <div className="relative" ref={projectSelectorRef}>
      <button
        type="button"
        onClick={() => setProjectSelectorOpen((o) => !o)}
        className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
          selectedProjectId
            ? "border-[#22D3EE]/40 bg-[#22D3EE]/10 text-[#22D3EE] hover:bg-[#22D3EE]/20"
            : "border-border/50 bg-card/40 text-muted-foreground hover:bg-card/80 hover:text-foreground"
        }`}
        title={selectedProjectId ? "Change project" : "Link to a project"}
      >
        <Folder className="h-3.5 w-3.5" />
        <span className="max-w-[140px] truncate">{selectedProjectName ?? "Link Project"}</span>
        <ChevronDown className={`h-3 w-3 transition-transform ${projectSelectorOpen ? "rotate-180" : ""}`} />
      </button>
      {projectSelectorOpen && (
        <div className="absolute right-0 top-full z-50 mt-1 w-72 rounded-xl border border-border/60 bg-[#0D1117] shadow-xl overflow-hidden">
          {/* Context-aware header */}
          <div className="px-3 py-2.5 border-b border-border/30 bg-[#111720]">
            <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              {selectedProjectId ? "Linked project" : "Link this conversation to a project"}
            </p>
          </div>

          {/* Unlink option — only shown when a project IS currently selected */}
          {selectedProjectId && (
            <button
              type="button"
              onClick={() => handleSelectProject(null)}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:bg-card/80 hover:text-destructive transition-colors border-b border-border/30"
            >
              <span className="h-3.5 w-3.5 rounded-sm border border-border/50 flex items-center justify-center text-[9px] shrink-0">✕</span>
              Unlink project
            </button>
          )}

          {/* Project list or empty state */}
          {projects.length === 0 ? (
            <div className="px-4 py-5 text-center space-y-2">
              <Folder className="h-6 w-6 text-muted-foreground/50 mx-auto" />
              <p className="text-xs font-medium text-foreground">No projects yet</p>
              <p className="text-[11px] text-muted-foreground">Create a project to track and organise your conversations.</p>
              <Link
                href="/projects"
                onClick={() => setProjectSelectorOpen(false)}
                className="inline-flex items-center gap-1.5 mt-1 px-3 py-1.5 rounded-lg bg-[#22D3EE]/15 border border-[#22D3EE]/30 text-[#22D3EE] text-xs font-semibold hover:bg-[#22D3EE]/25 transition-colors"
              >
                <Plus className="h-3 w-3" />
                Create your first project
              </Link>
            </div>
          ) : (
            <div className="max-h-52 overflow-y-auto">
              {projects.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelectProject(p)}
                  className={`w-full flex items-center gap-2 px-3 py-2.5 text-xs text-left transition-colors hover:bg-card/80 ${
                    selectedProjectId === p.id ? "bg-[#22D3EE]/10 text-[#22D3EE]" : "text-foreground"
                  }`}
                >
                  <Folder className="h-3.5 w-3.5 shrink-0 text-[#22D3EE]" />
                  <div className="truncate flex-1">
                    <span className="font-medium">{p.name}</span>
                    {p.description && (
                      <span className="text-muted-foreground text-[10px] truncate block mt-0.5">
                        {p.description.slice(0, 48)}
                      </span>
                    )}
                  </div>
                  {selectedProjectId === p.id && (
                    <span className="ml-auto text-[#22D3EE] text-[10px] shrink-0">✓</span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Footer: manage + new project */}
          <div className="border-t border-border/30 px-3 py-2 flex items-center justify-between gap-2">
            <Link
              href="/projects"
              className="text-[10px] text-muted-foreground hover:text-[#22D3EE] flex items-center gap-1 transition-colors"
              onClick={() => setProjectSelectorOpen(false)}
            >
              <ExternalLink className="h-2.5 w-2.5" />
              Manage all projects
            </Link>
            <Link
              href="/projects"
              className="text-[10px] text-[#22D3EE] hover:underline flex items-center gap-1 font-medium transition-colors"
              onClick={() => setProjectSelectorOpen(false)}
            >
              <Plus className="h-2.5 w-2.5" />
              New project
            </Link>
          </div>
        </div>
      )}
    </div>
  );


  if (!isLoaded) {
    return (
      <div className="space-y-6 flex flex-col h-full">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agent Playground</h1>
          <p className="text-muted-foreground mt-1">Interact directly with models, test prompt templates, and analyze sandbox behavior logs.</p>
        </div>
        <div className="border border-dashed border-border/60 bg-card/20 p-12 text-center flex flex-col items-center justify-center rounded-xl min-h-[400px]">
          <RefreshCw className="h-6 w-6 animate-spin text-primary mb-2 mx-auto" />
          <p className="text-xs text-muted-foreground font-mono">Restoring playground session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 flex flex-col h-full">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agent Playground</h1>
          <p className="text-muted-foreground mt-1">Interact directly with models, test prompt templates, and analyze sandbox behavior logs.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <ProjectSelector />
          {messages.length > 0 && (
            <Button variant="outline" size="sm" onClick={handleNewConversation} className="border-[#202833] bg-[#111720] hover:bg-[#182232] text-xs font-mono">
              <Plus className="mr-1.5 h-3.5 w-3.5 text-[#22D3EE]" />
              New Conversation
            </Button>
          )}
        </div>
      </div>

      {messages.length === 0 ? (
        <div className="border border-dashed border-border/60 bg-card/20 p-8 sm:p-12 text-center flex flex-col items-center justify-center rounded-xl min-h-[400px]">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
            <Terminal className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-foreground">Start your first conversation</h3>
          <p className="text-sm mt-2 mb-6 text-muted-foreground max-w-sm">
            Interactive model sandbox environment allowing real-time prompt execution testing against connected AI runtime providers.
          </p>

          {selectedProjectName && (
            <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
              <span>Linked to:</span>
              <ProjectBadge name={selectedProjectName} />
            </div>
          )}

          {sessions.length > 0 && (
            <div className="w-full max-w-md mb-6 text-left border border-[#202833] bg-[#0D1117]/80 rounded-xl p-3.5 shadow-sm">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <History className="h-3.5 w-3.5 text-[#22D3EE]" />
                  Saved Conversations ({sessions.length})
                </span>
                <span className="text-[10px] text-muted-foreground font-mono">Click to resume</span>
              </div>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {sessions.slice(0, 5).map((s) => (
                  <div key={s.id} onClick={() => handleSelectSession(s)} className="flex items-center justify-between p-2 rounded-lg border border-border/40 bg-card/40 hover:bg-card/90 transition-all cursor-pointer group text-xs">
                    <div className="flex items-center gap-2 truncate pr-2 min-w-0">
                      <MessageSquare className="h-3.5 w-3.5 text-[#22D3EE] shrink-0" />
                      <div className="min-w-0">
                        <span className="font-medium text-foreground truncate block">{s.title}</span>
                        {s.projectName && (
                          <span className="text-[10px] text-[#22D3EE] flex items-center gap-0.5 truncate">
                            <Folder className="h-2.5 w-2.5 shrink-0" />
                            {s.projectName}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] text-muted-foreground font-mono">{s.messages.length} msgs</span>
                      <button type="button" onClick={(e) => handleDeleteSession(e, s.id)} className="opacity-0 group-hover:opacity-100 hover:text-destructive transition p-1" title="Delete conversation">
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap justify-center gap-2 max-w-lg mb-6">
            {templates.map((t) => (
              <Button key={t.name} variant="outline" size="sm" onClick={() => applyTemplate(t.prompt)} className="text-xs">{t.name}</Button>
            ))}
          </div>

          <form onSubmit={handleSend} className="w-full max-w-md flex gap-2">
            <Input placeholder="Ask the AI model a coding question..." value={input} onChange={(e) => setInput(e.target.value)} className="bg-card/40" />
            <Button type="submit" className="gap-2"><Send className="h-4 w-4" />Send</Button>
          </form>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[600px]">
          {/* Left Column: Settings & History */}
          <div className="lg:col-span-1 border border-border/40 bg-card/30 rounded-xl p-4 flex flex-col gap-4 overflow-y-auto">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold uppercase text-muted-foreground tracking-wider">Model Settings</h3>
              </div>
              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Model</label>
                  <select value={model} onChange={(e) => setModel(e.target.value)} className="text-sm p-2 rounded border bg-background">
                    <option value="gemini-flash-latest">Google Gemini Flash</option>
                    <option value="claude-3-5-sonnet">Anthropic Claude 3.5 Sonnet</option>
                    <option value="gpt-4o">OpenAI GPT-4o</option>
                    <option value="deepseek-r1">OpenRouter (DeepSeek R1)</option>
                    <option value="llama-3.3-70b">Groq (Llama 3.3 70B)</option>
                    <option value="command-r-plus">Cohere Command R+</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Temperature ({temperature})</label>
                  <input type="range" min="0" max="1" step="0.1" value={temperature} onChange={(e) => setTemperature(e.target.value)} className="w-full" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Max Tokens</label>
                  <Input type="number" value={maxTokens} onChange={(e) => setMaxTokens(e.target.value)} className="text-sm bg-background" />
                </div>
              </div>
            </div>

            {sessions.length > 0 && (
              <div className="border-t border-border/40 pt-3 flex-1 flex flex-col min-h-[140px]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase text-muted-foreground tracking-wider flex items-center gap-1">
                    <History className="h-3 w-3 text-[#22D3EE]" />
                    History ({sessions.length})
                  </span>
                  <button type="button" onClick={handleNewConversation} className="text-[11px] text-[#22D3EE] hover:underline flex items-center gap-0.5">
                    <Plus className="h-3 w-3" /> New
                  </button>
                </div>
                <div className="space-y-1 overflow-y-auto max-h-40 pr-1 text-xs">
                  {sessions.map((s) => {
                    const isActive = s.id === activeSessionId;
                    return (
                      <div key={s.id} onClick={() => handleSelectSession(s)} className={`p-2 rounded-lg border transition-all cursor-pointer flex items-start justify-between group ${isActive ? "bg-primary/15 border-primary/40 text-primary font-medium" : "border-border/30 bg-card/20 hover:bg-card/60 text-muted-foreground hover:text-foreground"}`}>
                        <div className="min-w-0 flex-1 pr-1">
                          <span className="truncate block text-[11px]">{s.title}</span>
                          {s.projectName && (
                            <span className={`text-[10px] flex items-center gap-0.5 truncate mt-0.5 ${isActive ? "text-primary/70" : "text-[#22D3EE]/70"}`}>
                              <Folder className="h-2.5 w-2.5 shrink-0" />
                              {s.projectName}
                            </span>
                          )}
                        </div>
                        <button type="button" onClick={(e) => handleDeleteSession(e, s.id)} className="opacity-0 group-hover:opacity-100 hover:text-destructive transition p-0.5 shrink-0 mt-0.5" title="Delete session">
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <Button variant="outline" size="sm" onClick={handleNewConversation} className="mt-auto text-xs border-[#202833] hover:bg-[#182232]">
              Start New Chat
            </Button>
          </div>

          {/* Right Column: Chat Stream */}
          <div className="lg:col-span-3 border border-border/40 bg-card/30 rounded-xl p-4 flex flex-col justify-between overflow-hidden">
            {selectedProjectName && (
              <div className="flex items-center gap-2 pb-3 mb-2 border-b border-border/30">
                <span className="text-xs text-muted-foreground">Project:</span>
                <ProjectBadge name={selectedProjectName} />
              </div>
            )}

            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {messages.map((m, idx) => (
                <div key={idx} className={`relative p-3 rounded-lg flex flex-col gap-1 text-sm ${m.role === "user" ? "bg-primary/10 border border-primary/20 ml-8" : "bg-card border border-border/50 mr-8 group"}`}>
                  {m.role === "assistant" && <CopyButton text={m.content} />}
                  <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground mb-1">
                    <span className="flex items-center gap-1">
                      {m.role === "user" ? <UserIcon className="h-3.5 w-3.5 text-primary" /> : <Bot className="h-3.5 w-3.5 text-primary" />}
                      {m.role === "user" ? "You" : "AI Assistant"}
                    </span>
                    <span className={m.role === "assistant" ? "mr-6" : ""}>{m.timestamp}</span>
                  </div>
                  {m.role === "user" ? (
                    <div className="whitespace-pre-wrap font-mono text-xs">{m.content}</div>
                  ) : (
                    <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-border/50 text-[13px] leading-normal text-foreground/90">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                    </div>
                  )}
                </div>
              ))}

              {sending && (
                <div className="p-3 rounded-lg flex flex-col gap-2 text-sm bg-card border border-border/50 mr-8 animate-in fade-in-50 duration-300">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
                    <Bot className="h-3.5 w-3.5 text-primary" />
                    <span>AI Assistant is thinking...</span>
                  </div>
                  <div className="flex items-center gap-1.5 py-1 px-1">
                    <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 rounded-full bg-primary animate-bounce" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} className="flex gap-2 pt-4 border-t border-border/40">
              <Input placeholder="Type your message or prompt..." value={input} onChange={(e) => setInput(e.target.value)} disabled={sending} className="bg-card/40" />
              <Button type="submit" disabled={sending}>
                {sending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
