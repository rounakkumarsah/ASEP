"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import { MessageSquare, Code, Terminal, Send, Loader2, Bot, User as UserIcon, Plus, GitCompare, Paperclip, Wrench, Cpu, Workflow, Play, FileText, FolderGit2, ShieldAlert, Gauge, Zap, BarChart2, AlertTriangle, Square, GitBranch, ExternalLink, Check, RefreshCw, GitPullRequest, CheckCircle2, Sparkles, PanelLeftOpen, PanelRightOpen, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import { useWorkspaceStore } from "@/lib/stores/workspaceStore";
import { useChatHistoryStore } from "@/lib/stores/chatHistoryStore";
import { useSidebarStore } from "@/lib/stores/sidebarStore";
import { useVoiceTyping } from "@/hooks/useVoiceTyping";
const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });
import ReactMarkdown from 'react-markdown';
import { ExplorationCard } from "./ExplorationCard";

// Dynamic imports for components that use browser-only APIs (DOM/canvas/WebGL)
// ssr:false prevents hydration mismatches and React Error Boundary crashes
const WorkflowVisualizer = dynamic(
  () => import("./WorkflowVisualizer").then((m) => ({ default: m.WorkflowVisualizer })),
  { ssr: false, loading: () => (
    <div className="flex-1 flex flex-col items-center justify-center gap-6 p-8">
      <div className="w-full max-w-md space-y-4">
        {[1,2,3,4].map(i => (
          <div key={i} className="flex items-center gap-4">
            <div className="h-10 w-10 rounded-full bg-muted/30 animate-pulse flex-shrink-0" />
            <div className="flex-1 h-8 rounded-lg bg-muted/20 animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  )}
);
const PlaygroundTerminal = dynamic(
  () => import("./PlaygroundTerminal").then((m) => ({ default: m.PlaygroundTerminal })),
  { ssr: false, loading: () => (
    <div className="flex-1 bg-[#090B0F] font-mono text-xs p-4 space-y-2">
      <div className="h-3 bg-green-900/40 rounded w-2/3 animate-pulse" />
      <div className="h-3 bg-green-900/40 rounded w-1/2 animate-pulse" />
      <div className="h-3 bg-green-900/40 rounded w-3/4 animate-pulse" />
      <div className="h-3 bg-green-900/20 rounded w-1/3 animate-pulse mt-4" />
      <div className="flex items-center gap-2 mt-4">
        <span className="text-green-400">$</span>
        <div className="h-3 bg-green-900/40 rounded w-40 animate-pulse" />
      </div>
    </div>
  )}
);

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const MODELS = [
  { id: 'gemini-flash-latest', name: 'Gemini 1.5 Flash' },
  { id: 'gemini-pro-latest', name: 'Gemini 1.5 Pro' },
  { id: 'claude-3-5-sonnet-20240620', name: 'Claude 3.5 Sonnet' },
  { id: 'gpt-4o', name: 'GPT-4o' }
];

const TOOLS = [
  { id: 'web', name: 'Web Search' },
  { id: 'docs', name: 'Official Docs' },
  { id: 'github', name: 'GitHub Repos' },
  { id: 'sandbox', name: 'Python Sandbox' }
];

export function CenterWorkspace() {
  const {
    messages,
    addMessage,
    isThinking,
    setIsThinking,
    activeCenterTab,
    setActiveCenterTab,
    model,
    setActiveLeftTab,
    setModel,
    toggleTool,
    activeTools,
    researchMode,
    activeNode,
    setActiveNode,
    addCompletedNode,
    resetActiveNodes,
    setPhaseMap,
    addTerminalLog,
    clearTerminalLogs,
    githubRepo,
    setGithubActiveFile,
    environmentMode,
    setLocalSecrets,
    setCredentialsStatus,
    phaseMap,
    tokenUsagePerPhase,
    setTokenUsagePerPhase,
    tokenBudgets,
    setTokenBudgets,
    tokenSavings,
    setTokenSavings,
    budgetExceeded,
    setBudgetExceeded,
    appUrl,
    setAppUrl,
    githubConnected,
    setGithubConnected,
    githubUser,
    setGithubUser,
    githubSyncStatus,
    setGithubSyncStatus,
    githubLastSyncedSha,
    setGithubLastSyncedSha,
    githubDiffs,
    setGithubDiffs,
    githubProposals,
    setGithubProposals,
    githubActiveRepo,
    setGithubActiveRepo,
    githubActiveBranch,
    setGithubActiveBranch,
    selectedProjectId,
    selectedProjectName,
    activeSkills,
    skillCitations,
    addExplorationEvent,
    setPhaseExploration,
    voiceMetrics,
  } = usePlaygroundStore();
  const { isLeftPanelOpen, toggleLeftPanel, isRightPanelOpen, toggleRightPanel } = useSidebarStore();
  const [input, setInput] = React.useState("");
  const [cmdMenu, setCmdMenu] = React.useState<'tool' | 'model' | null>(null);
  const [artifactCode, setArtifactCode] = React.useState<string>("");
  const [toastMessage, setToastMessage] = React.useState<string | null>(null);

  // Universal Voice Typing
  const initialVoiceInputRef = React.useRef<string>("");
  const currentInputRef = React.useRef(input);
  currentInputRef.current = input;

  const { isListening, isTranscribing, toggleListening } = useVoiceTyping({
    onTranscript: (transcript, isFinal) => {
      setInput(() => {
        const base = initialVoiceInputRef.current;
        const combined = base.trim() ? `${base.trim()} ${transcript.trim()}` : transcript.trim();
        if (isFinal) {
          initialVoiceInputRef.current = combined;
        }
        return combined;
      });
    },
    onToast: (msg) => {
      setToastMessage(msg);
      setTimeout(() => setToastMessage(null), 4500);
    },
  });

  React.useEffect(() => {
    if (isListening) {
      initialVoiceInputRef.current = currentInputRef.current;
    }
  }, [isListening]);
  const [clarificationPrompt, setClarificationPrompt] = React.useState<string | null>(null);
  const [clarificationThreadId, setClarificationThreadId] = React.useState<string | null>(null);
  const [clarificationInput, setClarificationInput] = React.useState<string>("");
  const [mcpConfirmation, setMcpConfirmation] = React.useState<{ tool: string; server?: string; message: string } | null>(null);
  const [isApprovingMcp, setIsApprovingMcp] = React.useState(false);

  const handleApproveMcpTool = async (allow: boolean) => {
    if (!mcpConfirmation) return;
    if (!allow) {
      addTerminalLog("system", `[MCP Security] User denied execution of tool: ${mcpConfirmation.tool}`);
      setMcpConfirmation(null);
      return;
    }
    setIsApprovingMcp(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "") : "";
      await fetch(`${apiBase}/api/v1/mcp/tools/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('asep_auth_token') || sessionStorage.getItem('asep_auth_token') || ''}`
        },
        body: JSON.stringify({
          session_id: "default_session",
          tool_name: mcpConfirmation.tool,
        }),
      });
      addTerminalLog("system", `[MCP Security] Approved '${mcpConfirmation.tool}' for this session.`);
      setMcpConfirmation(null);
    } catch (err) {
      console.error("Failed to approve MCP tool:", err);
    } finally {
      setIsApprovingMcp(false);
    }
  };

  const handleApproveBudget = () => {
    addTerminalLog("system", "[Token Budget] Operator approved phase budget continuation.");
    handleResume(undefined, "approve");
  };
  const [cmdIndex, setCmdIndex] = React.useState(0);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [securityFindings, setSecurityFindings] = React.useState<any[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [editorInstance, setEditorInstance] = React.useState<any>(null);

  // GitHub Push & Sync Dialog State
  const [showPushModal, setShowPushModal] = React.useState(false);
  const [pushRepoName, setPushRepoName] = React.useState(selectedProjectName ? selectedProjectName.toLowerCase().replace(/\s+/g, "-") : "my-app");
  const [pushCreateNew, setPushCreateNew] = React.useState(true);
  const [pushPrivate, setPushPrivate] = React.useState(true);
  const [pushAutoReadme, setPushAutoReadme] = React.useState(true);
  const [pushLanguage, setPushLanguage] = React.useState("python");
  const [pushTaskSummary, setPushTaskSummary] = React.useState(selectedProjectName || "Application built with ASEP");
  const [pushBranchSlug, setPushBranchSlug] = React.useState(selectedProjectName ? selectedProjectName.toLowerCase().replace(/\s+/g, "-").slice(0, 20) : "feature-app");
  const [pushLoading, setPushLoading] = React.useState(false);
  const [pushError, setPushError] = React.useState<string | null>(null);
  const [pushResult, setPushResult] = React.useState<{ repo_url: string; branch: string; commit_sha: string; pr_url: string } | null>(null);
  const [userRepoList, setUserRepoList] = React.useState<Array<{ name: string; full_name: string }>>([]);
  const [fetchingRepos, setFetchingRepos] = React.useState(false);
  const [syncLoading, setSyncLoading] = React.useState(false);

  // Sync GitHub status from API on mount
  React.useEffect(() => {
    async function fetchGhStatus() {
      try {
        const token = localStorage.getItem("asep_auth_token") || sessionStorage.getItem("asep_auth_token") || "";
        const res = await fetch("/api/v1/integrations/github/status", {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (res.ok) {
          const data = await res.json();
          setGithubConnected(data.connected);
          if (data.connected && data.username) {
            setGithubUser({
              username: data.username,
              avatar_url: data.avatar_url || "",
              email: data.email,
              scopes: data.scopes || [],
            });
          }
        }
      } catch (err) {
        console.warn("Could not check GitHub integration status", err);
      }
    }
    fetchGhStatus();
  }, [setGithubConnected, setGithubUser]);

  // Auto-sync active conversation to chatHistoryStore
  React.useEffect(() => {
    if (messages.length > 0) {
      const activeWs = useWorkspaceStore.getState().getActiveWorkspace();
      const currentChatId = useChatHistoryStore.getState().activeSessionId || `chat_${Date.now()}`;
      useChatHistoryStore.getState().saveOrUpdateSession({
        id: currentChatId,
        messages,
        projectId: selectedProjectId,
        projectName: selectedProjectName,
        workspaceId: activeWs.id,
        workspaceName: activeWs.name,
      });
    }
  }, [messages, selectedProjectId, selectedProjectName]);

  const fetchUserRepos = async () => {
    setFetchingRepos(true);
    try {
      const token = localStorage.getItem("asep_auth_token") || sessionStorage.getItem("asep_auth_token") || "";
      const res = await fetch("/api/v1/integrations/github/repos", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setUserRepoList(data.repos || []);
      }
    } catch (err) {
      console.warn("Failed to fetch user repos", err);
    } finally {
      setFetchingRepos(false);
    }
  };

  const handlePushToGitHub = async () => {
    if (!pushRepoName.trim()) return;
    setPushLoading(true);
    setPushError(null);
    try {
      const token = localStorage.getItem("asep_auth_token") || sessionStorage.getItem("asep_auth_token") || "";
      const codeToPush = artifactCode || "# Generated by ASEP\nprint('Hello from ASEP')";
      const res = await fetch("/api/v1/integrations/github/push", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          repo_name: pushRepoName.trim(),
          create_new: pushCreateNew,
          private: pushPrivate,
          auto_readme: pushAutoReadme,
          language: pushLanguage,
          task_summary: pushTaskSummary.trim() || "Application built with ASEP",
          task_slug: pushBranchSlug.trim() || "app",
          files: {
            "main.py": codeToPush,
          },
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to push to GitHub");
      }
      setPushResult({
        repo_url: data.repo_url,
        branch: data.branch,
        commit_sha: data.commit_sha,
        pr_url: data.pr_url,
      });
      setGithubActiveRepo(pushRepoName);
      setGithubActiveBranch(data.branch);
      setGithubLastSyncedSha(data.commit_sha);
      setGithubSyncStatus("synced");
      addTerminalLog("success", `[GitHub Push] Successfully pushed commit ${data.commit_sha.slice(0, 7)} to branch '${data.branch}'.`);
      setToastMessage("Pushed to GitHub branch successfully!");
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Failed to push to GitHub";
      setPushError(errMsg);
      addTerminalLog("error", `[GitHub Push Error] ${errMsg}`);
    } finally {
      setPushLoading(false);
    }
  };

  const handleSyncFromGitHub = async () => {
    const targetRepo = githubActiveRepo || pushRepoName;
    if (!targetRepo) {
      setToastMessage("Please push to a repository first.");
      setTimeout(() => setToastMessage(null), 3000);
      return;
    }
    setSyncLoading(true);
    try {
      const token = localStorage.getItem("asep_auth_token") || sessionStorage.getItem("asep_auth_token") || "";
      const res = await fetch("/api/v1/integrations/github/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          repo_name: targetRepo,
          branch: githubActiveBranch || "asep/app",
          local_files: {
            "main.py": artifactCode || "",
          },
          last_synced_sha: githubLastSyncedSha,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to sync with GitHub");
      }
      setGithubSyncStatus(data.status);
      setGithubDiffs(data.diffs || {});
      setGithubProposals(data.reconciliation_proposals || {});
      setGithubLastSyncedSha(data.latest_remote_sha);

      if (data.status === "synced") {
        setToastMessage("Workspace is fully synced with GitHub!");
        addTerminalLog("success", "[GitHub Sync] Workspace is up to date with remote.");
      } else {
        setToastMessage(`GitHub sync status: ${data.status.toUpperCase()}. Incoming changes opened in Diff Viewer.`);
        addTerminalLog("system", `[GitHub Sync] Status '${data.status}': ${data.changed_files?.length || 0} files modified on remote.`);
        setActiveCenterTab("diff");
      }
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Failed to sync with GitHub";
      setToastMessage(`GitHub Sync Error: ${errMsg}`);
      addTerminalLog("error", `[GitHub Sync Error] ${errMsg}`);
      setTimeout(() => setToastMessage(null), 4000);
    } finally {
      setSyncLoading(false);
    }
  };

  const handleAcceptReconciliation = (filename: string) => {
    const proposal = githubProposals[filename];
    if (proposal) {
      setArtifactCode(proposal);
      const remainingDiffs = { ...githubDiffs };
      delete remainingDiffs[filename];
      setGithubDiffs(remainingDiffs);
      if (Object.keys(remainingDiffs).length === 0) {
        setGithubSyncStatus("synced");
      }
      addTerminalLog("success", `[GitHub Reconciliation] Reconciled and merged changes for '${filename}'.`);
      setToastMessage(`Reconciled changes for ${filename}`);
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  const jumpToLine = (file: string, line: number) => {
    setActiveCenterTab("artifacts");
    if (editorInstance) {
      setTimeout(() => {
        editorInstance.revealLineInCenter(line);
        editorInstance.setPosition({ lineNumber: line, column: 1 });
        editorInstance.focus();
      }, 100);
    }
  };

  const handleRunArtifact = async () => {
    setActiveCenterTab("terminal");
    clearTerminalLogs();
    addTerminalLog("input", "Running main.py in isolated sandbox...");
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "") : "";
      const endpoint = `${apiBase}/api/v1/sandbox/python/stream`;
      
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: artifactCode }),
      });
      
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      if (!res.body) return;
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr === "[DONE]") break;
            try {
              const data = JSON.parse(dataStr);
              if (data.type && data.text) {
                addTerminalLog(data.type, data.text);
              }
            } catch {
              // ignore partial json
            }
          }
        }
      }
    } catch (err) {
      addTerminalLog("error", `Sandbox execution failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleStopApp = async () => {
    if (!appUrl) return;
    const urlCopy = appUrl;
    const portMatch = urlCopy.match(/:(\d+)/);
    const port = portMatch ? parseInt(portMatch[1], 10) : undefined;

    addTerminalLog("system", `[Host Manager] Stopping app at ${urlCopy}...`);
    setAppUrl(null);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "") : "";
      await fetch(`${apiBase}/api/v1/host/stop`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem('asep_auth_token') || sessionStorage.getItem('asep_auth_token') || ''}`
        },
        body: JSON.stringify({ port }),
      });
      addTerminalLog("system", `⏹️ [Host Manager] App at ${urlCopy} was stopped.`);
    } catch (err) {
      addTerminalLog("system", `⚠️ [Host Manager] Stop request finished (${err instanceof Error ? err.message : String(err)})`);
    }
  };

  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const [cmdFilter, setCmdFilter] = React.useState('');

  const filteredCmdItems = React.useMemo(() => {
    if (cmdMenu === 'model') return MODELS.filter(m => m.name.toLowerCase().includes(cmdFilter.toLowerCase()));
    if (cmdMenu === 'tool') return TOOLS.filter(t => t.name.toLowerCase().includes(cmdFilter.toLowerCase()));
    return [];
  }, [cmdMenu, cmdFilter]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInput(val);
    const matchModel = val.match(/(?:^|\s)#(\w*)$/);
    const matchTool = val.match(/(?:^|\s)\/(\w*)$/);
    if (matchModel) { setCmdMenu('model'); setCmdFilter(matchModel[1]); setCmdIndex(0); }
    else if (matchTool) { setCmdMenu('tool'); setCmdFilter(matchTool[1]); setCmdIndex(0); }
    else { setCmdMenu(null); }
  };

  const handleCmdSelect = (item: { id: string; name: string }) => {
    if (cmdMenu === 'model') setModel(item.id);
    if (cmdMenu === 'tool') toggleTool(item.id);
    
    const replacement = cmdMenu === 'model' ? `#${cmdFilter}` : `/${cmdFilter}`;
    const lastIdx = input.lastIndexOf(replacement);
    if (lastIdx !== -1) {
      setInput(input.substring(0, lastIdx).trimEnd() + (input.substring(0, lastIdx).trimEnd() ? " " : ""));
    } else {
      setInput("");
    }
    setCmdMenu(null);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);


  const handleResume = async (e?: React.FormEvent, overrideDecision?: string) => {
    if (e) e.preventDefault();
    const decision = overrideDecision || clarificationInput;
    if (!decision.trim() || !clarificationThreadId || isThinking) return;

    addMessage({
      role: 'user',
      content: overrideDecision ? `[Approved continuation for phase budget]` : clarificationInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });

    setClarificationInput("");
    setClarificationPrompt(null);
    setBudgetExceeded(null);
    setIsThinking(true);

    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("asep_auth_token") || sessionStorage.getItem("asep_auth_token")
        : null;

      const apiBase = process.env.NEXT_PUBLIC_API_URL
        ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "")
        : "";
      const endpoint = `${apiBase}/api/v1/conversations/${clarificationThreadId}/resume`;

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify({ decision }),
      });

      if (!res.ok) throw new Error(`API returned HTTP ${res.status}: ${res.statusText}`);
      if (!res.body) return;

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let aiResponse = "";
      const streamMessages: string[] = [];
      

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr === "[DONE]") break;
            try {
              const data = JSON.parse(dataStr);
              if (data.event) {
                const nodeEntries = Object.entries(data.event);
                for (const [nodeName, updateVal] of nodeEntries) {
                  setActiveNode(nodeName);
                  addCompletedNode(nodeName);
                  const updateObj = updateVal as Record<string, unknown>;
                  const msg = updateObj.messages;
                  if (msg && Array.isArray(msg) && msg.length > 0) {
                    for (const m of msg) {
                      const messageItem = m as { role?: string; type?: string; name?: string; content?: string };
                      if (messageItem.role === "assistant" && messageItem.content && typeof messageItem.content === "string") {
                        aiResponse = messageItem.content;
                      } else if (messageItem.role === "system" && messageItem.content && typeof messageItem.content === "string") {
                        if (messageItem.content.includes("[Auto Router Toast]")) {
                          setToastMessage(messageItem.content.replace("[Auto Router Toast]", "").trim());
                          setTimeout(() => setToastMessage(null), 6000);
                        } else if (messageItem.content.includes("Phase map generated:")) {
                          const match = messageItem.content.match(/Phase map generated: (.*?)\./);
                          if (match && match[1]) {
                            const phases = match[1].split(" -> ");
                            setPhaseMap(phases);
                          }
                        } else if (messageItem.content.includes("[Clarification Required]")) {
                          setClarificationPrompt(messageItem.content.replace("[Clarification Required]", "").trim());
                        } else if (messageItem.content.includes("[Token Budgets]")) {
                          try {
                            const budgets = JSON.parse(messageItem.content.replace("[Token Budgets]", "").trim());
                            setTokenBudgets(budgets);
                          } catch {}
                        } else if (messageItem.content.includes("[Token Usage]")) {
                          try {
                            const usage = JSON.parse(messageItem.content.replace("[Token Usage]", "").trim());
                            setTokenUsagePerPhase(usage);
                          } catch {}
                        } else if (messageItem.content.includes("[Token Savings]")) {
                          try {
                            const savings = JSON.parse(messageItem.content.replace("[Token Savings]", "").trim());
                            setTokenSavings(savings);
                          } catch {}
                        } else if (messageItem.content.includes("[Token Budget Exceeded]")) {
                          const content = messageItem.content;
                          const matchPhase = content.match(/Phase '([^']+)'/);
                          const matchTokens = content.match(/consumed (\d+) tokens/);
                          const matchBudget = content.match(/allocated budget: (\d+)/);
                          const phase = matchPhase ? matchPhase[1] : "current_phase";
                          const used = matchTokens ? parseInt(matchTokens[1], 10) : 0;
                          const budget = matchBudget ? parseInt(matchBudget[1], 10) : 2500;
                          const percent = budget > 0 ? Math.round((used / budget) * 100) : 100;
                          setBudgetExceeded({
                            phase,
                            prompt: content.replace("[Token Budget Exceeded]", "").trim(),
                            used,
                            budget,
                            percent,
                          });
                        } else if (
                          messageItem.content.includes("[AST Slicer]") ||
                          messageItem.content.includes("[Diff Streamer]") ||
                          messageItem.content.includes("heal cycle #") ||
                          messageItem.content.includes("[Heal Cycle") ||
                          messageItem.content.includes("[Critic Execution]") ||
                          messageItem.content.includes("[Self-Healing")
                        ) {
                          addTerminalLog("system", messageItem.content);
                        } else if (messageItem.content.includes("[Research Node]")) {
                          addTerminalLog("system", "🔍 " + messageItem.content);
                        } else if (
                          messageItem.content.includes("[KB Query]") ||
                          messageItem.content.includes("[Knowledge Base Context]") ||
                          messageItem.content.includes("[Knowledge Base Preview]")
                        ) {
                          addTerminalLog("system", "📚 " + messageItem.content);

                        } else if (messageItem.content.includes("[Host Manager Status]")) {
                          const statusText = messageItem.content.replace("[Host Manager Status]", "").trim();
                          // Extract URL for live banner
                          const urlMatch = statusText.match(/https?:\/\/localhost:\d+/);
                          if (urlMatch) {
                            setAppUrl(urlMatch[0]);
                          }
                          if (statusText.startsWith("[OK]")) {
                            addTerminalLog("success", "🚀 " + statusText);
                            setActiveCenterTab("terminal");
                          } else {
                            addTerminalLog("system", "⚠️ " + statusText);
                          }
                        } else if (messageItem.content.includes("[Host Manager]")) {
                          addTerminalLog("system", "🖥️ " + messageItem.content);
                        } else if (messageItem.content.includes("[Host Manager Install]")) {
                          addTerminalLog("system", "📦 " + messageItem.content);

                        } else if (messageItem.content.includes("[MCP Confirmation Required]")) {
                          const promptText = messageItem.content.replace("[MCP Confirmation Required]", "").trim();
                          const matchTool = promptText.match(/(?:allow|tool)\s+([a-zA-Z0-9_\-\.]+)/i);
                          setMcpConfirmation({
                            tool: matchTool ? matchTool[1] : "mcp_tool",
                            message: promptText,
                          });
                        } else if (messageItem.content.includes("[MCP:")) {
                          addTerminalLog("system", messageItem.content);
                        } else if (messageItem.content.includes("[Security Audit]")) {
                          const findingsStr = messageItem.content.replace("[Security Audit]", "").trim();
                          try {
                              setSecurityFindings(JSON.parse(findingsStr));
                              setActiveCenterTab("security");
                          } catch {}
                        } else if (messageItem.content.includes("[Local Secrets]")) {
                          try {
                            const parsed = JSON.parse(messageItem.content.replace("[Local Secrets]", "").trim());
                            setLocalSecrets(Array.isArray(parsed) ? parsed : Object.keys(parsed || {}));
                          } catch {}
                        } else if (messageItem.content.includes("[Credentials Status]")) {
                          try {
                            setCredentialsStatus(JSON.parse(messageItem.content.replace("[Credentials Status]", "").trim()));
                          } catch {}
                        } else if (messageItem.content.includes("[Metrics]")) {
                          const metricsStr = messageItem.content.replace("[Metrics]", "").trim();
                          try {
                              const metrics = JSON.parse(metricsStr);
                              usePlaygroundStore.getState().setSessionMetrics(metrics);
                          } catch {}
                        } else if (messageItem.content.includes("[Explore Event]")) {
                          try {
                            const raw = messageItem.content.replace("[Explore Event]", "").trim();
                            const ev = JSON.parse(raw);
                            addExplorationEvent(ev);
                          } catch {}
                        } else if (messageItem.content.includes("[Explore Summary]")) {
                          try {
                            const raw = messageItem.content.replace("[Explore Summary]", "").trim();
                            const summary = JSON.parse(raw);
                            setPhaseExploration(summary.phase, summary);
                            addMessage({
                              role: "system",
                              content: `[Explore Summary] ${raw}`,
                              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                            });
                          } catch {}
                        }
                      }
                    }
                  }
                }
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

      addMessage({
        role: "assistant",
        content: aiResponse || "Resumed execution.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } catch (error) {
      addMessage({
        role: "assistant",
        content: `Error resuming run: ${error instanceof Error ? error.message : "Backend unavailable"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } finally {
      setIsThinking(false);
      setActiveNode(null);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;

    addMessage({
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    });

    const currentInput = input;
    setInput("");
    const newThreadId = "playground-session-" + Date.now();
    setClarificationThreadId(newThreadId);
    setIsThinking(true);
    resetActiveNodes();

    // ------------------------------------------------------------------
    // Polling-based run execution
    //
    // POST /conversations/run  →  { run_id, thread_id, status: "queued" }
    // GET  /conversations/run/{run_id}/status?cursor=N  every 1.5 s
    //      →  { status, events: [...], cursor }
    //
    // This replaces the broken SSE pattern that Vercel serverless buffers
    // entirely, causing fetch() to throw "Failed to fetch" before the agent
    // completes (30 s function timeout).
    // ------------------------------------------------------------------

    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("asep_auth_token") ||
            sessionStorage.getItem("asep_auth_token")
          : null;

      const apiBase = process.env.NEXT_PUBLIC_API_URL
        ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "")
        : "";

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      // 1. Submit the run — returns immediately with run_id
      const startRes = await fetch(`${apiBase}/api/v1/conversations/run`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          goal: currentInput,
          thread_id: newThreadId,
          research_mode: researchMode,
          environment_mode: environmentMode,
        }),
      });

      if (!startRes.ok) {
        throw new Error(`API returned HTTP ${startRes.status}: ${startRes.statusText}`);
      }

      const startData = await startRes.json() as { run_id: string; thread_id: string; status: string };
      const runId = startData.run_id;

      // 2. Poll for events and status
      let cursor = 0;
      let aiResponse = "";
      const streamMessages: string[] = [];
      let pollCount = 0;
      const MAX_POLLS = 240; // 240 * 1.5 s = 6 minutes max

      const processEventData = (data: Record<string, unknown>) => {
        if (!data.event) return;
        const nodeEntries = Object.entries(
          data.event as Record<string, unknown>,
        );
        for (const [nodeName, updateVal] of nodeEntries) {
          setActiveNode(nodeName);
          addCompletedNode(nodeName);

          if (updateVal && typeof updateVal === "object") {
            const updateObj = updateVal as Record<string, unknown>;
            const msg = updateObj.messages;
            if (msg && Array.isArray(msg) && msg.length > 0) {
              for (const m of msg) {
                const messageItem = m as {
                  role?: string;
                  type?: string;
                  name?: string;
                  content?: string;
                };
                if (
                  messageItem.role === "assistant" &&
                  messageItem.content &&
                  typeof messageItem.content === "string"
                ) {
                  aiResponse = messageItem.content;
                } else if (
                  messageItem.role === "system" &&
                  messageItem.content &&
                  typeof messageItem.content === "string"
                ) {
                  const c = messageItem.content;
                  if (c.includes("[Auto Router Toast]")) {
                    setToastMessage(c.replace("[Auto Router Toast]", "").trim());
                    setTimeout(() => setToastMessage(null), 6000);
                  } else if (c.includes("Phase map generated:")) {
                    const match = c.match(/Phase map generated: (.*?)\./);
                    if (match && match[1]) setPhaseMap(match[1].split(" -> "));
                  } else if (c.includes("[Clarification Required]")) {
                    setClarificationPrompt(
                      c.replace("[Clarification Required]", "").trim(),
                    );
                  } else if (c.includes("[Token Budgets]")) {
                    try {
                      setTokenBudgets(
                        JSON.parse(c.replace("[Token Budgets]", "").trim()),
                      );
                    } catch {}
                  } else if (c.includes("[Token Usage]")) {
                    try {
                      setTokenUsagePerPhase(
                        JSON.parse(c.replace("[Token Usage]", "").trim()),
                      );
                    } catch {}
                  } else if (c.includes("[Token Savings]")) {
                    try {
                      setTokenSavings(
                        JSON.parse(c.replace("[Token Savings]", "").trim()),
                      );
                    } catch {}
                  } else if (c.includes("[Token Budget Exceeded]")) {
                    const matchPhase = c.match(/Phase '([^']+)'/);
                    const matchTokens = c.match(/consumed (\d+) tokens/);
                    const matchBudget = c.match(/allocated budget: (\d+)/);
                    const used = matchTokens ? parseInt(matchTokens[1], 10) : 0;
                    const budget = matchBudget
                      ? parseInt(matchBudget[1], 10)
                      : 2500;
                    setBudgetExceeded({
                      phase: matchPhase ? matchPhase[1] : "current_phase",
                      prompt: c.replace("[Token Budget Exceeded]", "").trim(),
                      used,
                      budget,
                      percent: budget > 0 ? Math.round((used / budget) * 100) : 100,
                    });
                  } else if (
                    c.includes("[AST Slicer]") ||
                    c.includes("[Diff Streamer]") ||
                    c.includes("heal cycle #") ||
                    c.includes("[Heal Cycle") ||
                    c.includes("[Critic Execution]") ||
                    c.includes("[Self-Healing")
                  ) {
                    addTerminalLog("system", c);
                  } else if (c.includes("[Research Node]")) {
                    addTerminalLog("system", "🔍 " + c);
                  } else if (
                    c.includes("[KB Query]") ||
                    c.includes("[Knowledge Base Context]") ||
                    c.includes("[Knowledge Base Preview]")
                  ) {
                    addTerminalLog("system", "📚 " + c);
                  } else if (c.includes("[Host Manager Status]")) {
                    const statusText = c.replace("[Host Manager Status]", "").trim();
                    const urlMatch = statusText.match(/https?:\/\/localhost:\d+/);
                    if (urlMatch) setAppUrl(urlMatch[0]);
                    if (statusText.startsWith("[OK]")) {
                      addTerminalLog("success", "🚀 " + statusText);
                      setActiveCenterTab("terminal");
                    } else {
                      addTerminalLog("system", "⚠️ " + statusText);
                    }
                  } else if (c.includes("[Host Manager]")) {
                    addTerminalLog("system", "🖥️ " + c);
                  } else if (c.includes("[Host Manager Install]")) {
                    addTerminalLog("system", "📦 " + c);
                  } else if (c.includes("[MCP Confirmation Required]")) {
                    const promptText = c
                      .replace("[MCP Confirmation Required]", "")
                      .trim();
                    const matchTool = promptText.match(
                      /(?:allow|tool)\s+([a-zA-Z0-9_\-\.]+)/i,
                    );
                    setMcpConfirmation({
                      tool: matchTool ? matchTool[1] : "mcp_tool",
                      message: promptText,
                    });
                  } else if (c.includes("[MCP:")) {
                    addTerminalLog("system", c);
                  } else if (c.includes("[Local Secrets]")) {
                    try {
                      const parsed = JSON.parse(
                        c.replace("[Local Secrets]", "").trim(),
                      );
                      setLocalSecrets(
                        Array.isArray(parsed) ? parsed : Object.keys(parsed || {}),
                      );
                    } catch {}
                  } else if (c.includes("[Credentials Status]")) {
                    try {
                      setCredentialsStatus(
                        JSON.parse(c.replace("[Credentials Status]", "").trim()),
                      );
                    } catch {}
                  } else if (c.includes("[Metrics]")) {
                    try {
                      const metrics = JSON.parse(
                        c.replace("[Metrics]", "").trim(),
                      );
                      usePlaygroundStore.getState().setSessionMetrics({
                        estimatedCost: metrics.estimated_cost,
                        confidence: metrics.confidence || null,
                      });
                    } catch {}
                  } else if (c.includes("[Explore Event]")) {
                    try {
                      const ev = JSON.parse(
                        c.replace("[Explore Event]", "").trim(),
                      );
                      addExplorationEvent(ev);
                    } catch {}
                  } else if (c.includes("[Explore Summary]")) {
                    try {
                      const raw = c.replace("[Explore Summary]", "").trim();
                      const summary = JSON.parse(raw);
                      setPhaseExploration(summary.phase, summary);
                      addMessage({
                        role: "system",
                        content: `[Explore Summary] ${raw}`,
                        timestamp: new Date().toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        }),
                      });
                    } catch {}
                  } else {
                    streamMessages.push(c);
                  }
                } else if (
                  messageItem.type === "tool" &&
                  messageItem.name === "github" &&
                  messageItem.content
                ) {
                  try {
                    const parsed = JSON.parse(messageItem.content);
                    if (parsed.success && parsed.result && parsed.result.files) {
                      usePlaygroundStore.getState().setGithubRepo({
                        url: parsed.result.repo_name || "GitHub Repo",
                        files: parsed.result.files,
                        activeFile: null,
                      });
                      if (parsed.result.readme) setArtifactCode(parsed.result.readme);
                    } else if (
                      parsed.success &&
                      parsed.result &&
                      parsed.result.file &&
                      parsed.result.content
                    ) {
                      usePlaygroundStore
                        .getState()
                        .setGithubActiveFile(parsed.result.file);
                      setArtifactCode(parsed.result.content);
                      setActiveCenterTab("artifacts");
                    }
                  } catch {}
                }
              }
            }
          }
        }
      };

      let currentStatus = "running";
      while (currentStatus === "running" && pollCount < MAX_POLLS) {
        pollCount++;
        
        const stepRes = await fetch(
          `${apiBase}/api/v1/conversations/run/${runId}/step`,
          { 
            method: "POST", 
            headers,
            body: JSON.stringify({ thread_id: newThreadId })
          }
        );
        
        if (!stepRes.ok) {
           throw new Error(`API returned HTTP ${stepRes.status}: ${stepRes.statusText}`);
        }
        
        const stepData = await stepRes.json();
        if (stepData.events) {
          for (const ev of stepData.events) {
            try {
              processEventData(ev);
            } catch {}
          }
        }
        currentStatus = stepData.status;
      }

      if (aiResponse) {
        const codeMatch = aiResponse.match(/```(?:python|bash|sh|txt|)\n([\s\S]*?)```/);
        if (codeMatch && codeMatch[1]) setArtifactCode(codeMatch[1].trim());
      }

      addMessage({
        role: "assistant",
        content:
          aiResponse ||
          (streamMessages.length > 0
            ? streamMessages.join("\n\n")
            : "Task processed through LangGraph multi-agent execution pipeline."),
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      });
    } catch (error) {
      console.error("LangGraph run execution error:", error);
      addMessage({
        role: "assistant",
        content: `Error executing LangGraph run: ${error instanceof Error ? error.message : "Backend unavailable"}`,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      });
    } finally {
      setIsThinking(false);
      setActiveNode(null);
    }
  };

  const getModelName = (modelId: string) => {
    if (modelId === 'claude-3-5-sonnet-20240620') return 'Claude 3.5 Sonnet';
    if (modelId === 'gemini-flash-latest') return 'Gemini 1.5 Flash';
    if (modelId === 'deepseek-coder') return 'DeepSeek Coder V2';
    if (modelId === 'gpt-4o') return 'GPT-4o';
    if (modelId === 'auto-router') return 'Auto Router (Cost/Perf)';
    return modelId;
  };

  return (
    <div className="h-full w-full flex flex-col bg-[#0D1117] relative">
      {toastMessage && (
        <div className="absolute top-4 right-4 bg-orange-500 text-white px-4 py-2 rounded-md shadow-xl z-50 animate-in fade-in slide-in-from-top-4 flex items-center gap-2 text-sm font-medium border border-orange-400">
          <Bot className="h-4 w-4" />
          {toastMessage}
        </div>
      )}
      <Tabs value={activeCenterTab} onValueChange={setActiveCenterTab} className="flex-1 flex flex-col min-h-0">
        <div className="px-3 sm:px-4 py-2 border-b border-border/40 bg-background/50 backdrop-blur flex items-center justify-between gap-2 overflow-x-auto no-scrollbar scroll-smooth min-w-0">
          <div className="flex items-center gap-2 shrink-0">
            {!isLeftPanelOpen && (
              <Button
                variant="outline"
                size="sm"
                onClick={toggleLeftPanel}
                className="h-9 px-2.5 gap-1.5 text-xs font-mono text-muted-foreground hover:text-primary border-border/60 hover:bg-accent shrink-0 shadow-xs hidden md:inline-flex"
                title="Expand Configuration Panel (Ctrl+[)"
                aria-label="Expand Configuration Panel"
              >
                <PanelLeftOpen className="h-3.5 w-3.5 text-primary" />
                <span className="font-sans font-medium text-xs">Config</span>
              </Button>
            )}

            <TabsList className="bg-muted/50 h-9 p-1 shrink-0 flex-nowrap">
              <TabsTrigger value="chat" className="text-xs gap-1.5 sm:gap-2 px-2.5 sm:px-3">
                <MessageSquare className="h-3.5 w-3.5 shrink-0" />
                <span>Chat</span>
              </TabsTrigger>
              <TabsTrigger value="workflow" className="text-xs gap-1.5 sm:gap-2 px-2.5 sm:px-3">
                <Workflow className="h-3.5 w-3.5 shrink-0" />
                <span><span className="hidden sm:inline">Visual </span>Workflow</span>
              </TabsTrigger>
              <TabsTrigger value="artifacts" className="text-xs gap-1.5 sm:gap-2 px-2.5 sm:px-3">
                <Code className="h-3.5 w-3.5 shrink-0" />
                <span>Artifacts</span>
              </TabsTrigger>
              <TabsTrigger value="diff" className="text-xs gap-1.5 sm:gap-2 px-2.5 sm:px-3">
                <GitCompare className="h-3.5 w-3.5 shrink-0" />
                <span>Diff<span className="hidden sm:inline"> Viewer</span></span>
              </TabsTrigger>
              <TabsTrigger value="terminal" className="text-xs gap-1.5 sm:gap-2 px-2.5 sm:px-3">
                <Terminal className="h-3.5 w-3.5 shrink-0" />
                <span>Terminal</span>
              </TabsTrigger>
              <TabsTrigger value="metrics" className="text-xs gap-1.5 sm:gap-2 px-2.5 sm:px-3">
                <Gauge className="h-3.5 w-3.5 shrink-0" />
                <span><span className="hidden sm:inline">Token </span>Metrics</span>
              </TabsTrigger>
              {securityFindings.length > 0 && (
                <TabsTrigger value="security" className="text-xs gap-1.5 sm:gap-2 px-2.5 sm:px-3 text-destructive">
                  <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
                  <span>Security<span className="hidden sm:inline"> Audit</span></span>
                </TabsTrigger>
              )}
            </TabsList>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {activeSkills && activeSkills.length > 0 && (
              <div className="hidden md:flex items-center gap-1.5 shrink-0">
                <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider hidden lg:inline">Active Skills:</span>
                {activeSkills.map((s) => (
                  <Badge key={s} variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30 text-[11px] font-mono py-0.5 px-2 flex items-center gap-1 shrink-0">
                    <Sparkles className="w-2.5 h-2.5" />
                    [SKILL: {s}]
                  </Badge>
                ))}
              </div>
            )}
            {!isRightPanelOpen && (
              <Button
                variant="outline"
                size="sm"
                onClick={toggleRightPanel}
                className="h-9 px-2.5 gap-1.5 text-xs font-mono text-muted-foreground hover:text-[#22D3EE] border-border/60 hover:bg-accent shrink-0 shadow-xs hidden xl:inline-flex"
                title="Expand Execution Trace (Ctrl+])"
                aria-label="Expand Execution Trace"
              >
                <span className="font-sans font-medium text-xs">Trace</span>
                <PanelRightOpen className="h-3.5 w-3.5 text-[#22D3EE]" />
              </Button>
            )}
          </div>
        </div>

        <div className="flex-1 min-h-0 relative flex flex-col">
          <TabsContent value="chat" className="flex-1 mt-0 border-0 flex-col data-[state=active]:flex data-[state=inactive]:hidden min-h-0">
            <ScrollArea className="flex-1 h-full">
              <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto space-y-6 pb-32">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-[40vh] text-center space-y-4">
                    <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                      <Bot className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold">How can I help you build today?</h3>
                      <p className="text-sm text-muted-foreground mt-1 max-w-sm">Use the AI Engineering Workspace to generate code, run agents, and analyze your repository.</p>
                    </div>
                  </div>
                ) : (
                  messages.map((msg, idx) => {
                    if (msg.content?.startsWith('[Skill Activated]')) {
                      return (
                        <div key={idx} className="flex justify-center my-1.5 animate-in fade-in">
                          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-950/40 border border-purple-500/30 text-purple-300 text-xs font-mono shadow-sm">
                            <Sparkles className="h-3.5 w-3.5 text-purple-400 shrink-0" />
                            <span>{msg.content}</span>
                          </div>
                        </div>
                      );
                    }
                    if (msg.content?.startsWith('[Skill Reference]')) {
                      return (
                        <div key={idx} className="flex justify-center my-1 animate-in fade-in">
                          <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-[11px] font-mono shadow-sm">
                            <FileText className="h-3 w-3 text-cyan-400 shrink-0" />
                            <span>{msg.content}</span>
                          </div>
                        </div>
                      );
                    }
                    if (msg.content?.startsWith('[Explore Summary]')) {
                      return (
                        <div key={idx} className="w-full my-2 animate-in fade-in">
                          <ExplorationCard content={msg.content} />
                        </div>
                      );
                    }

                    return (
                      <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.role === 'assistant' && (
                          <div className="h-8 w-8 rounded bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
                            <Bot className="h-4 w-4 text-primary" />
                          </div>
                        )}
                        
                        <div className={`group relative max-w-[85%] rounded-xl px-4 py-3 text-sm shadow-sm ${
                          msg.role === 'user' 
                            ? 'bg-[#22D3EE]/10 text-foreground border border-[#22D3EE]/20' 
                            : 'bg-card border border-border/50 text-card-foreground'
                        }`}>
                          <div className="prose prose-sm dark:prose-invert max-w-none">
                            <ReactMarkdown>
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                          {skillCitations && skillCitations.length > 0 && msg.role === 'assistant' && idx === messages.length - 1 && (
                            <div className="mt-2 pt-2 border-t border-border/30 flex flex-wrap gap-1">
                              {skillCitations.map((cit, cIdx) => (
                                <span key={cIdx} className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40">
                                  {cit}
                                </span>
                              ))}
                            </div>
                          )}
                          <span className="text-[9px] text-muted-foreground absolute -bottom-4 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            {msg.timestamp}
                          </span>
                        </div>

                        {msg.role === 'user' && (
                          <div className="h-8 w-8 rounded bg-muted flex items-center justify-center shrink-0 border border-border/50">
                            <UserIcon className="h-4 w-4 text-muted-foreground" />
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
                {clarificationPrompt && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 my-4 max-w-[85%]">
                      <div className="flex gap-3 mb-3 text-amber-500 font-medium">
                        <ShieldAlert className="h-5 w-5" />
                        <span>Action Required</span>
                      </div>
                      <div className="text-sm text-foreground mb-4">
                        {clarificationPrompt}
                      </div>
                      <form onSubmit={handleResume} className="flex gap-2">
                        <input
                          type="text"
                          value={clarificationInput}
                          onChange={(e) => setClarificationInput(e.target.value)}
                          placeholder="Enter credentials or type 'mock'..."
                          className="flex-1 bg-background/50 border border-border rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500/50"
                          disabled={isThinking}
                        />
                        <Button type="submit" disabled={isThinking || !clarificationInput.trim()} className="bg-amber-500 hover:bg-amber-600 text-white shrink-0">
                          Submit
                        </Button>
                      </form>
                    </div>
                  )}
                  {mcpConfirmation && (
                    <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-4 my-4 max-w-[85%] space-y-3">
                      <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
                        <ShieldAlert className="h-5 w-5 text-cyan-400 shrink-0" />
                        <span>Security Confirmation: External MCP Tool</span>
                      </div>
                      <div className="text-sm text-foreground space-y-1">
                        <p>
                          An agent requested to call external tool{" "}
                          <code className="px-1.5 py-0.5 rounded bg-muted/60 font-mono text-xs text-cyan-300">
                            {mcpConfirmation.tool}
                          </code>
                          .
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {mcpConfirmation.message || "Model Context Protocol tools can access external systems or execute actions outside the sandbox."}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 pt-1">
                        <Button
                          size="sm"
                          onClick={() => handleApproveMcpTool(true)}
                          disabled={isApprovingMcp}
                          className="bg-cyan-500 hover:bg-cyan-600 text-black font-semibold text-xs h-8"
                        >
                          {isApprovingMcp ? "Approving..." : "Allow for This Session"}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleApproveMcpTool(false)}
                          disabled={isApprovingMcp}
                          className="text-xs h-8"
                        >
                          Deny
                        </Button>
                      </div>
                    </div>
                  )}
                  {budgetExceeded && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 my-4 max-w-[85%] space-y-3">
                      <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
                        <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
                        <span>Token Budget Exceeded — Continuation Approval Required</span>
                      </div>
                      <div className="text-sm text-foreground space-y-1">
                        <p>
                          Phase: <code className="px-1.5 py-0.5 rounded bg-muted/60 font-mono text-xs text-amber-300 capitalize">{budgetExceeded.phase.replace(/_/g, " ")}</code>
                        </p>
                        <p className="text-xs text-muted-foreground">{budgetExceeded.prompt}</p>
                        <div className="flex flex-wrap items-center gap-4 text-xs font-mono pt-1 text-muted-foreground">
                          <span>Consumed: <strong className="text-foreground">{budgetExceeded.used.toLocaleString()}</strong> tokens</span>
                          <span>Quota: <strong className="text-foreground">{budgetExceeded.budget.toLocaleString()}</strong> tokens</span>
                          <span className="text-amber-400 font-bold">({budgetExceeded.percent}% used)</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 pt-1">
                        <Button
                          size="sm"
                          onClick={handleApproveBudget}
                          disabled={isThinking}
                          className="bg-amber-500 hover:bg-amber-600 text-black font-semibold text-xs h-8"
                        >
                          Approve Budget & Continue
                        </Button>
                      </div>
                    </div>
                  )}
                  {isThinking && (
                  <div className="flex gap-4 justify-start">
                    <div className="h-8 w-8 rounded bg-[#22D3EE]/10 flex items-center justify-center shrink-0 border border-[#22D3EE]/20">
                      <Loader2 className="h-4 w-4 text-[#22D3EE] animate-spin" />
                    </div>
                    <div className="bg-card border border-border/50 rounded-xl px-4 py-3 text-sm flex items-center gap-3 text-muted-foreground shadow-sm">
                      <div className="flex gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#22D3EE] animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1.5 h-1.5 rounded-full bg-[#22D3EE] animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1.5 h-1.5 rounded-full bg-[#22D3EE] animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span>
                        {activeNode ? (
                          <span>
                            Active Node: <strong className="text-[#22D3EE] font-mono text-xs uppercase">{activeNode}</strong>
                          </span>
                        ) : (
                          "Orchestrating agents..."
                        )}
                      </span>
                      <button
                        type="button"
                        onClick={() => setActiveCenterTab("workflow")}
                        className="text-[10px] text-[#22D3EE] hover:underline flex items-center gap-1 ml-2 border border-[#22D3EE]/30 bg-[#22D3EE]/10 px-2 py-0.5 rounded transition-colors"
                      >
                        <Workflow className="h-2.5 w-2.5" /> View Graph
                      </button>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="workflow" className="flex-1 mt-0 border-0 flex flex-col data-[state=active]:flex data-[state=inactive]:hidden min-h-0 h-full">
            <WorkflowVisualizer />
          </TabsContent>

          <TabsContent value="artifacts" className="flex-1 mt-0 border-0 data-[state=active]:flex data-[state=inactive]:hidden min-h-0">
            <div className="w-64 border-r border-border/40 bg-background/50 p-4 overflow-y-auto">
              {githubRepo ? (
                <>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                    <FolderGit2 className="h-4 w-4" /> {githubRepo.url}
                  </h4>
                  <div className="space-y-1">
                    {githubRepo.files.slice(0, 1000).map((file) => (
                      <div 
                        key={file} 
                        className={`text-xs p-1.5 rounded flex items-center gap-2 cursor-pointer font-mono truncate ${githubRepo.activeFile === file ? 'bg-primary/20 text-primary' : 'hover:bg-accent/50 text-muted-foreground'}`}
                        title={file}
                        onClick={() => {
                          if (!githubRepo) return;
                          setGithubActiveFile(file);
                          setArtifactCode("Loading..."); // Trigger skeleton
                          const fetchFile = async () => {
                            try {
                              const rawUrl = `https://raw.githubusercontent.com/${githubRepo.url}/HEAD/${file}`;
                              const controller = new AbortController();
                              const timeoutId = setTimeout(() => controller.abort(), 8000);
                              const res = await fetch(rawUrl, { signal: controller.signal });
                              clearTimeout(timeoutId);
                              if (!res.ok) throw new Error("Failed");
                              const text = await res.text();
                              setArtifactCode(text);
                            } catch {
                              setToastMessage("Failed to load file. Network error.");
                              setArtifactCode("// Error loading file");
                            }
                          };
                          fetchFile();
                        }}
                      >
                        <FileText className="h-3 w-3 flex-shrink-0" />
                        <span className="truncate">{file}</span>
                      </div>
                    ))}
                    {githubRepo.files.length > 1000 && (
                      <div className="text-xs p-1.5 rounded text-muted-foreground italic truncate">
                        ...and {githubRepo.files.length - 1000} more files
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Files</h4>
                  <div className="space-y-1">
                    <div className="text-xs p-1.5 rounded bg-accent text-accent-foreground flex items-center justify-between group cursor-pointer font-mono">
                      <div className="flex items-center gap-2">
                        <Code className="h-3 w-3 text-emerald-400" /> main.py
                      </div>
                      <button onClick={handleRunArtifact} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-primary/20 text-primary rounded" title="Run in Sandbox">
                        <Play className="h-3 w-3" />
                      </button>
                    </div>
                    <div className="text-xs p-1.5 rounded hover:bg-accent/50 text-muted-foreground flex items-center gap-2 cursor-pointer font-mono">
                      <Code className="h-3 w-3 text-amber-400" /> config.json
                    </div>
                  </div>
                </>
              )}
            </div>
            <div className="flex-1 bg-[#1E1E1E] relative">
              {artifactCode === "Loading..." ? (
                <div className="absolute inset-0 p-6 space-y-4">
                  <div className="h-4 bg-muted/20 rounded w-1/3 animate-pulse" />
                  <div className="h-4 bg-muted/20 rounded w-1/2 animate-pulse" />
                  <div className="h-4 bg-muted/20 rounded w-2/3 animate-pulse" />
                  <div className="h-4 bg-muted/20 rounded w-1/4 animate-pulse" />
                  <div className="h-4 bg-muted/20 rounded w-3/4 animate-pulse" />
                </div>
              ) : (
                <Editor
                  height="100%"
                  defaultLanguage="python"
                  theme="vs-dark"
                  value={artifactCode}
                  onChange={(val) => setArtifactCode(val || "")}
                  onMount={(editor) => setEditorInstance(editor)}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 13,
                    wordWrap: "on",
                  }}
                />
              )}
              {securityFindings.some(f => f.severity === 'critical') && (
                <div className="absolute top-4 left-4 right-32 bg-destructive/90 text-white px-4 py-2 rounded shadow-lg flex items-center justify-between text-sm backdrop-blur-sm z-50">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4" />
                    <span className="font-bold">Security Block:</span> CRITICAL vulnerabilities detected. Code execution and copying disabled.
                  </div>
                  <Button variant="outline" size="sm" className="h-6 text-xs bg-transparent border-white/30 hover:bg-white/10 text-white" onClick={() => setActiveCenterTab('security')}>
                    View Findings
                  </Button>
                </div>
              )}
              {/* GitHub Status & Actions Banner */}
              <div className="absolute top-4 right-4 flex items-center gap-2 z-40">
                {/* Sync status badge */}
                {githubSyncStatus !== 'idle' && (
                  <Badge
                    variant="outline"
                    className={`text-[11px] gap-1 px-2 py-0.5 font-mono ${
                      githubSyncStatus === 'synced'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : githubSyncStatus === 'behind'
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    }`}
                  >
                    {githubSyncStatus === 'synced' && <Check className="h-3 w-3" />}
                    {githubSyncStatus === 'behind' && <RefreshCw className="h-3 w-3" />}
                    {githubSyncStatus === 'conflict' && <AlertTriangle className="h-3 w-3" />}
                    {githubSyncStatus.toUpperCase()}
                  </Badge>
                )}

                {/* Sync from GitHub button */}
                <Button
                  onClick={handleSyncFromGitHub}
                  disabled={syncLoading}
                  variant="outline"
                  size="sm"
                  className="bg-[#202833]/80 hover:bg-[#2A3441] text-zinc-200 border-border/60 text-xs gap-1.5 shadow-sm"
                  title="Pull latest changes from GitHub"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${syncLoading ? 'animate-spin text-cyan-400' : 'text-cyan-400'}`} />
                  Sync
                </Button>

                {/* Push to GitHub button */}
                <Button
                  onClick={() => {
                    fetchUserRepos();
                    setShowPushModal(true);
                  }}
                  size="sm"
                  className="bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700 text-xs gap-1.5 shadow-sm"
                  title="Push artifacts to asep/<slug> branch on GitHub"
                >
                  <GitBranch className="h-3.5 w-3.5 text-emerald-400" />
                  Push to GitHub
                </Button>

                <Button 
                  onClick={() => {
                    if (securityFindings.some(f => f.severity === 'critical')) return;
                    navigator.clipboard.writeText(artifactCode);
                    setToastMessage("Code copied to clipboard");
                    setTimeout(() => setToastMessage(null), 3000);
                  }}
                  className={`bg-[#202833] hover:bg-[#2A3441] text-white shadow-lg gap-2 ${securityFindings.some(f => f.severity === 'critical') ? 'opacity-50 cursor-not-allowed' : ''}`}
                  size="sm"
                  disabled={securityFindings.some(f => f.severity === 'critical')}
                >
                  <Code className="h-4 w-4" fill="currentColor" /> Copy
                </Button>

                <Button 
                  onClick={handleRunArtifact}
                  className={`bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg gap-2 ${securityFindings.some(f => f.severity === 'critical') ? 'opacity-50 cursor-not-allowed' : ''}`}
                  size="sm"
                  disabled={securityFindings.some(f => f.severity === 'critical')}
                >
                  <Play className="h-4 w-4" fill="currentColor" /> Run Code
                </Button>
              </div>

              {/* Push Result Banner */}
              {pushResult && (
                <div className="absolute bottom-4 left-4 right-4 bg-zinc-950/90 border border-emerald-500/40 rounded-xl p-3 flex items-center justify-between text-xs text-zinc-200 backdrop-blur z-40 shadow-2xl">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>
                      Pushed to branch <code className="font-mono text-emerald-300 font-semibold">{pushResult.branch}</code> (commit: <code className="font-mono">{pushResult.commit_sha.slice(0, 7)}</code>)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href={pushResult.repo_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-zinc-300 hover:text-white underline flex items-center gap-1"
                    >
                      View on GitHub <ExternalLink className="h-3 w-3" />
                    </a>
                    {pushResult.pr_url && (
                      <a
                        href={pushResult.pr_url}
                        target="_blank"
                        rel="noreferrer"
                        className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-2.5 py-1 rounded font-medium flex items-center gap-1 transition-colors"
                      >
                        <GitPullRequest className="h-3 w-3" /> Open PR
                      </a>
                    )}
                    <button
                      onClick={() => setPushResult(null)}
                      className="text-zinc-500 hover:text-zinc-300 text-xs px-1"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}

              {/* Push to GitHub Dialog Modal */}
              {showPushModal && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                  <div className="bg-background border border-border/80 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
                    <div className="flex items-center justify-between border-b border-border/40 pb-3">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-zinc-900 border border-border flex items-center justify-center text-emerald-400">
                          <GitBranch className="h-4 w-4" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm text-foreground">Push to GitHub</h3>
                          <p className="text-[11px] text-muted-foreground">Atomic Git Data commit with branch isolation</p>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setShowPushModal(false);
                          setPushError(null);
                        }}
                        className="text-muted-foreground hover:text-foreground text-sm"
                      >
                        ✕
                      </button>
                    </div>

                    {/* Mode: New vs Existing */}
                    <div className="flex rounded-lg bg-muted/40 p-1 text-xs">
                      <button
                        type="button"
                        onClick={() => setPushCreateNew(true)}
                        className={`flex-1 py-1.5 font-medium rounded-md transition-all ${
                          pushCreateNew ? "bg-background shadow text-foreground" : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        Create New Repo
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setPushCreateNew(false);
                          fetchUserRepos();
                        }}
                        className={`flex-1 py-1.5 font-medium rounded-md transition-all ${
                          !pushCreateNew ? "bg-background shadow text-foreground" : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        Push to Existing Repo
                      </button>
                    </div>

                    {/* Fields */}
                    {pushCreateNew ? (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-semibold text-muted-foreground">Repository Name</label>
                          <Input
                            placeholder="e.g. my-awesome-app"
                            value={pushRepoName}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPushRepoName(e.target.value)}
                            className="text-xs mt-1"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-xs font-semibold text-muted-foreground">Visibility</label>
                            <select
                              value={pushPrivate ? "private" : "public"}
                              onChange={(e) => setPushPrivate(e.target.value === "private")}
                              className="w-full text-xs p-2 rounded-md border border-input bg-background mt-1"
                            >
                              <option value="private">Private</option>
                              <option value="public">Public</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-xs font-semibold text-muted-foreground">Language (.gitignore)</label>
                            <select
                              value={pushLanguage}
                              onChange={(e) => setPushLanguage(e.target.value)}
                              className="w-full text-xs p-2 rounded-md border border-input bg-background mt-1"
                            >
                              <option value="python">Python</option>
                              <option value="typescript">TypeScript / Node</option>
                              <option value="go">Go</option>
                              <option value="rust">Rust</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
                            <span>Select Repository</span>
                            {fetchingRepos && <span className="text-[10px] text-muted-foreground">Loading...</span>}
                          </label>
                          {userRepoList.length > 0 ? (
                            <select
                              value={pushRepoName}
                              onChange={(e) => setPushRepoName(e.target.value)}
                              className="w-full text-xs p-2 rounded-md border border-input bg-background mt-1"
                            >
                              {userRepoList.map((r) => (
                                <option key={r.full_name} value={r.full_name}>
                                  {r.full_name}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <Input
                              placeholder="owner/repo-name"
                              value={pushRepoName}
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPushRepoName(e.target.value)}
                              className="text-xs mt-1"
                            />
                          )}
                        </div>
                      </div>
                    )}

                    {/* Branch & Safety Invariant Card */}
                    <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 space-y-1.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                          <GitBranch className="h-3.5 w-3.5" /> Target Branch:
                        </span>
                        <code className="font-mono text-emerald-300 font-semibold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                          asep/{pushBranchSlug || "feature"}
                        </code>
                      </div>
                      <p className="text-[11px] text-muted-foreground">
                        🛡️ Safety Rule: Direct pushes to <code className="text-rose-400 font-mono">main</code> are blocked. ASEP pushes to an isolated branch with PR generation.
                      </p>
                    </div>

                    {/* Commit Message Preview */}
                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold text-muted-foreground uppercase">Commit Message</label>
                      <div className="p-2 rounded bg-muted/30 border border-border/40 font-mono text-[11px] text-foreground">
                        ASEP: {pushTaskSummary || "Autonomous Application"} [phase: deploy]
                      </div>
                    </div>

                    {pushError && (
                      <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-lg">
                        {pushError}
                      </p>
                    )}

                    {/* Modal Footer */}
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setShowPushModal(false);
                          setPushError(null);
                        }}
                        className="text-xs"
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        disabled={pushLoading || !pushRepoName.trim()}
                        onClick={handlePushToGitHub}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs gap-1.5"
                      >
                        {pushLoading ? (
                          <>
                            <Loader2 className="h-3.5 w-3.5 animate-spin" /> Pushing to GitHub...
                          </>
                        ) : (
                          <>
                            <GitBranch className="h-3.5 w-3.5" /> Push to asep/{pushBranchSlug || "app"}
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="diff" className="flex-1 mt-0 border-0 p-6 data-[state=active]:flex data-[state=inactive]:hidden flex-col min-h-0 overflow-y-auto">
            {Object.keys(githubDiffs).length > 0 ? (
              <div className="space-y-6 max-w-4xl mx-auto w-full">
                <div className="flex items-center justify-between border-b border-border/50 pb-3">
                  <div>
                    <h3 className="text-base font-semibold flex items-center gap-2">
                      <GitCompare className="h-5 w-5 text-emerald-400" />
                      Incoming Remote Changes from GitHub
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Target branch: <code className="font-mono text-emerald-400">{githubActiveBranch || "asep/app"}</code>. Review changes before reconciling.
                    </p>
                  </div>
                  <Badge
                    variant="outline"
                    className={`font-mono text-xs ${
                      githubSyncStatus === 'conflict'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {githubSyncStatus.toUpperCase()}
                  </Badge>
                </div>

                {Object.entries(githubDiffs).map(([filename, diffText]) => (
                  <div key={filename} className="border border-border/50 rounded-xl overflow-hidden bg-background shadow-md space-y-0">
                    <div className="bg-muted/60 px-4 py-2.5 border-b border-border/50 flex justify-between items-center text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <FileText className="h-3.5 w-3.5 text-primary" />
                        <span className="font-semibold text-foreground">{filename}</span>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleAcceptReconciliation(filename)}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs h-7 gap-1"
                      >
                        <Check className="h-3 w-3" /> Accept & Merge
                      </Button>
                    </div>

                    {/* Unified Diff View */}
                    <div className="p-4 font-mono text-xs overflow-x-auto text-left leading-relaxed max-h-64 overflow-y-auto bg-zinc-950">
                      {diffText.split("\n").map((line, idx) => {
                        const isAdd = line.startsWith("+") && !line.startsWith("+++");
                        const isDel = line.startsWith("-") && !line.startsWith("---");
                        const isHunk = line.startsWith("@@");

                        return (
                          <div
                            key={idx}
                            className={`px-2 py-0.5 -mx-2 ${
                              isAdd
                                ? "bg-emerald-500/15 text-emerald-400"
                                : isDel
                                ? "bg-rose-500/15 text-rose-400"
                                : isHunk
                                ? "bg-cyan-500/15 text-cyan-400 font-semibold"
                                : "text-zinc-300"
                            }`}
                          >
                            {line || " "}
                          </div>
                        );
                      })}
                    </div>

                    {/* Reconciliation proposal preview */}
                    {githubProposals[filename] && (
                      <div className="border-t border-border/40 p-4 bg-muted/10 space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                            <Workflow className="h-3.5 w-3.5 text-cyan-400" />
                            Reconciliation Proposal (Preserves workspace code & merges incoming edits)
                          </p>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              navigator.clipboard.writeText(githubProposals[filename]);
                              setToastMessage("Copied reconciled version to clipboard");
                              setTimeout(() => setToastMessage(null), 3000);
                            }}
                            className="text-xs h-6 text-muted-foreground hover:text-foreground"
                          >
                            Copy Reconciled
                          </Button>
                        </div>
                        <pre className="p-3 bg-zinc-950/80 rounded-lg text-xs font-mono text-zinc-300 overflow-x-auto max-h-48 border border-border/30">
                          {githubProposals[filename]}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="text-center mb-8">
                  <GitCompare className="h-8 w-8 mx-auto mb-3 opacity-50 text-emerald-500" />
                  <h3 className="text-lg font-medium text-foreground">No active diffs to show</h3>
                  <p className="text-sm">Click &quot;Sync from GitHub&quot; on the Artifacts panel to check for remote updates.</p>
                </div>
                
                <div className="w-full max-w-3xl border border-border/50 rounded-lg overflow-hidden bg-background shadow-xl opacity-75">
                  <div className="bg-muted px-4 py-2 border-b border-border/50 flex justify-between items-center text-xs font-mono">
                    <span>Example: how incoming changes will appear</span>
                    <span className="text-muted-foreground">backend/main.py</span>
                  </div>
                  <div className="p-4 font-mono text-xs overflow-x-auto text-left leading-relaxed">
                    <div className="text-muted-foreground">@@ -15,7 +15,8 @@</div>
                    <div className="text-foreground"> def initialize_agent():</div>
                    <div className="bg-destructive/10 text-destructive-foreground px-2 py-0.5 -mx-4">-    return LangGraph(checkpointer=MemorySaver())</div>
                    <div className="bg-emerald-500/10 text-emerald-500 px-2 py-0.5 -mx-4">+    # Now utilizing Postgres-backed persistent memory</div>
                    <div className="bg-emerald-500/10 text-emerald-500 px-2 py-0.5 -mx-4">+    return LangGraph(checkpointer=AsyncPostgresSaver(pool))</div>
                    <div className="text-foreground"> </div>
                    <div className="text-foreground"> async def run_agent():</div>
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="terminal" className="flex-1 mt-0 border-0 data-[state=active]:flex data-[state=inactive]:hidden min-h-0 flex-col overflow-hidden">
            {appUrl && (
              <div className="flex items-center gap-3 px-4 py-2 bg-emerald-950/60 border-b border-emerald-800/40 text-emerald-400 font-mono text-xs shrink-0">
                <span className="flex items-center gap-1.5">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span className="font-semibold text-emerald-300">[OK]</span>
                  App running at
                </span>
                <a
                  href={appUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-300 hover:text-emerald-100 underline underline-offset-2 font-semibold transition-colors"
                >
                  {appUrl}
                </a>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    onClick={() => { navigator.clipboard?.writeText(appUrl); }}
                    className="text-emerald-400 hover:text-emerald-200 text-[10px] border border-emerald-800/50 hover:bg-emerald-900/40 px-2 py-0.5 rounded transition-colors"
                    title="Copy URL"
                  >
                    Copy
                  </button>
                  <button
                    onClick={handleStopApp}
                    className="text-rose-400 hover:text-rose-200 text-[10px] border border-rose-800/50 bg-rose-950/40 hover:bg-rose-900/60 px-2 py-0.5 rounded transition-colors flex items-center gap-1 font-sans font-medium"
                    title="Stop running application"
                  >
                    <Square className="h-2.5 w-2.5 fill-current" />
                    Stop App
                  </button>
                </div>
              </div>
            )}
            <PlaygroundTerminal />
          </TabsContent>

          <TabsContent value="security" className="flex-1 mt-0 border-0 p-8 data-[state=active]:flex data-[state=inactive]:hidden flex-col min-h-0 overflow-y-auto">
            <div className="max-w-5xl mx-auto w-full space-y-6 pb-20">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold flex items-center gap-2 text-destructive"><ShieldAlert className="h-5 w-5" /> Security Audit Findings</h2>
                  <p className="text-sm text-muted-foreground mt-1">Review critical vulnerabilities and hardcoded secrets found in the generated code.</p>
                </div>
                {securityFindings.some(f => f.severity === 'critical') && (
                  <div className="bg-destructive/10 text-destructive border border-destructive/20 px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4" />
                    CRITICAL VULNERABILITIES DETECTED
                  </div>
                )}
              </div>
              
              <div className="border border-border/50 rounded-xl overflow-hidden bg-card">
                <table className="w-full text-sm text-left">
                  <thead className="bg-muted/50 text-muted-foreground text-xs uppercase border-b border-border/50">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Severity</th>
                      <th className="px-4 py-3 font-semibold">Location</th>
                      <th className="px-4 py-3 font-semibold">Description</th>
                      <th className="px-4 py-3 font-semibold">Suggested Fix</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {securityFindings.map((finding, idx) => (
                      <tr key={idx} className="hover:bg-muted/20 transition-colors">
                        <td className="px-4 py-3 align-top">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                            finding.severity === 'critical' ? 'bg-destructive/20 text-destructive border border-destructive/30' :
                            finding.severity === 'high' ? 'bg-orange-500/20 text-orange-500 border border-orange-500/30' :
                            finding.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30' :
                            'bg-blue-500/20 text-blue-500 border border-blue-500/30'
                          }`}>
                            {finding.severity}
                          </span>
                        </td>
                        <td 
                          className="px-4 py-3 align-top font-mono text-xs whitespace-nowrap cursor-pointer hover:underline text-[#22D3EE]" 
                          onClick={() => jumpToLine(finding.file, finding.line)}
                        >
                          {finding.file}:{finding.line}
                        </td>
                        <td className="px-4 py-3 align-top font-medium text-foreground">
                          {finding.description}
                        </td>
                        <td className="px-4 py-3 align-top text-muted-foreground">
                          {finding.suggested_fix}
                        </td>
                      </tr>
                    ))}
                    {securityFindings.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                          No security vulnerabilities detected.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="metrics" className="flex-1 mt-0 border-0 overflow-y-auto data-[state=active]:block data-[state=inactive]:hidden min-h-0 p-6">
            <div className="max-w-5xl mx-auto space-y-6 pb-12">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-border/40 pb-4">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2 text-foreground">
                    <Gauge className="h-5 w-5 text-[#22D3EE]" />
                    Token Efficiency & Per-Phase Quota Telemetry
                  </h2>
                  <p className="text-xs text-muted-foreground mt-1">
                    First-class token optimization engine with AST Slicing, Diff-Only Streaming, and per-phase pause gates.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <Zap className="h-3 w-3" />
                    Adaptive AST Active
                  </span>
                </div>
              </div>

              {/* Efficiency Stat Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-xl border border-border/40 bg-card/40 p-4 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground font-medium">AST Slicing Saved</span>
                    <Code className="h-4 w-4 text-[#22D3EE]" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-[#22D3EE] mt-2">
                    {(tokenSavings?.ast_slicing || 0).toLocaleString()}
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1">Tokens spared by symbol extraction</p>
                </div>

                <div className="rounded-xl border border-border/40 bg-card/40 p-4 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground font-medium">Diff Streaming Saved</span>
                    <GitCompare className="h-4 w-4 text-purple-400" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-purple-400 mt-2">
                    {(tokenSavings?.diff_streaming || 0).toLocaleString()}
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1">Tokens spared by unified diffs</p>
                </div>

                <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-4 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-emerald-300 font-medium">Total Tokens Saved</span>
                    <Zap className="h-4 w-4 text-emerald-400" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-emerald-400 mt-2">
                    {((tokenSavings?.total_saved || (tokenSavings?.ast_slicing || 0) + (tokenSavings?.diff_streaming || 0))).toLocaleString()}
                  </div>
                  <p className="text-[11px] text-emerald-400/80 mt-1">Context reduction across all phases</p>
                </div>
              </div>

              {/* Phase Budget Comparison Table / Chart */}
              <div className="rounded-xl border border-border/40 bg-card/30 overflow-hidden">
                <div className="p-4 border-b border-border/30 flex items-center justify-between">
                  <h3 className="text-sm font-semibold flex items-center gap-2">
                    <BarChart2 className="h-4 w-4 text-primary" />
                    Per-Phase Token Quota vs Consumed Breakdown
                  </h3>
                  <span className="text-xs text-muted-foreground font-mono">
                    {Object.keys(tokenUsagePerPhase || {}).length} phases tracked
                  </span>
                </div>

                <div className="p-4 space-y-4">
                  {(() => {
                    const defaultPhases = ["research", "clarification_gate", "blueprint", "scaffold", "implement", "test", "security_audit", "deploy"];
                    const phases = Array.from(new Set([
                      ...(phaseMap && phaseMap.length > 0 ? phaseMap : defaultPhases),
                      ...Object.keys(tokenUsagePerPhase || {}),
                    ]));

                    return phases.map((phase) => {
                      const used = tokenUsagePerPhase?.[phase] || 0;
                      const budget = tokenBudgets?.[phase] || 2500;
                      const percent = Math.round((used / Math.max(1, budget)) * 100);
                      const isExceeded = used > budget;
                      const isWarning = percent >= 75 && !isExceeded;

                      return (
                        <div key={phase} className="p-3 rounded-lg bg-muted/20 border border-border/20 space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm capitalize text-foreground">
                                {phase.replace(/_/g, " ")}
                              </span>
                              {isExceeded ? (
                                <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-destructive/20 text-destructive border border-destructive/30">
                                  BUDGET EXCEEDED
                                </span>
                              ) : isWarning ? (
                                <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                  NEAR LIMIT ({percent}%)
                                </span>
                              ) : used > 0 ? (
                                <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                  OPTIMAL ({percent}%)
                                </span>
                              ) : (
                                <span className="text-[10px] px-2 py-0.5 rounded font-normal text-muted-foreground">
                                  Pending
                                </span>
                              )}
                            </div>
                            <div className="font-mono text-xs text-muted-foreground flex items-center gap-2">
                              <span className={isExceeded ? "text-destructive font-bold" : "text-foreground font-semibold"}>
                                {used.toLocaleString()}
                              </span>
                              <span>/</span>
                              <span>{budget.toLocaleString()} tokens</span>
                            </div>
                          </div>

                          {/* Progress Meter */}
                          <div className="w-full h-2 rounded-full bg-muted/60 overflow-hidden relative">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isExceeded
                                  ? "bg-destructive"
                                  : isWarning
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(100, percent)}%` }}
                            />
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>

              {/* Voice Transcription Metrics */}
              <div className="rounded-xl border border-border/40 bg-card/30 overflow-hidden">
                <div className="p-4 border-b border-border/30 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold flex items-center gap-2">
                      <Mic className="h-4 w-4 text-[#22D3EE]" />
                      Voice Transcription Telemetry
                    </h3>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Universal Voice Typing with 3-provider fallback chain (Groq → Gemini → OpenRouter) & Layer 1 Web Speech API.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-muted/50 border border-border/50 text-muted-foreground">
                      Total: {voiceMetrics?.totalTranscriptions || 0}
                    </span>
                  </div>
                </div>

                <div className="p-4 space-y-4">
                  {/* Provider Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {/* Groq Whisper */}
                    <div className="rounded-lg border border-border/40 bg-background/40 p-3 relative space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                          Groq Whisper
                        </span>
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0 bg-[#F55036]/10 text-[#F55036] border-[#F55036]/30">
                          Primary
                        </Badge>
                      </div>
                      <div className="text-xl font-bold font-mono text-foreground">
                        {voiceMetrics?.providerUsage?.groq || 0} <span className="text-[11px] font-normal text-muted-foreground">uses</span>
                      </div>
                      <div className="text-[11px] font-mono text-muted-foreground flex items-center justify-between pt-1 border-t border-border/30">
                        <span>Last Latency:</span>
                        <span className="text-[#22D3EE] font-semibold">
                          {voiceMetrics?.lastLatencyMs?.groq ? `${voiceMetrics.lastLatencyMs.groq}ms` : "—"}
                        </span>
                      </div>
                    </div>

                    {/* Gemini 2.0 Flash */}
                    <div className="rounded-lg border border-border/40 bg-background/40 p-3 relative space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                          Gemini 2.0 Flash
                        </span>
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0 bg-blue-500/10 text-blue-400 border-blue-500/30">
                          Backup 1
                        </Badge>
                      </div>
                      <div className="text-xl font-bold font-mono text-foreground">
                        {voiceMetrics?.providerUsage?.gemini || 0} <span className="text-[11px] font-normal text-muted-foreground">uses</span>
                      </div>
                      <div className="text-[11px] font-mono text-muted-foreground flex items-center justify-between pt-1 border-t border-border/30">
                        <span>Last Latency:</span>
                        <span className="text-blue-400 font-semibold">
                          {voiceMetrics?.lastLatencyMs?.gemini ? `${voiceMetrics.lastLatencyMs.gemini}ms` : "—"}
                        </span>
                      </div>
                    </div>

                    {/* OpenRouter */}
                    <div className="rounded-lg border border-border/40 bg-background/40 p-3 relative space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                          OpenRouter
                        </span>
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0 bg-purple-500/10 text-purple-400 border-purple-500/30">
                          Backup 2
                        </Badge>
                      </div>
                      <div className="text-xl font-bold font-mono text-foreground">
                        {voiceMetrics?.providerUsage?.openrouter || 0} <span className="text-[11px] font-normal text-muted-foreground">uses</span>
                      </div>
                      <div className="text-[11px] font-mono text-muted-foreground flex items-center justify-between pt-1 border-t border-border/30">
                        <span>Last Latency:</span>
                        <span className="text-purple-400 font-semibold">
                          {voiceMetrics?.lastLatencyMs?.openrouter ? `${voiceMetrics.lastLatencyMs.openrouter}ms` : "—"}
                        </span>
                      </div>
                    </div>

                    {/* Web Speech API */}
                    <div className="rounded-lg border border-border/40 bg-background/40 p-3 relative space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                          Web Speech API
                        </span>
                        <Badge variant="outline" className="text-[9px] px-1.5 py-0 bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                          Layer 1
                        </Badge>
                      </div>
                      <div className="text-xl font-bold font-mono text-foreground">
                        {voiceMetrics?.providerUsage?.webSpeech || 0} <span className="text-[11px] font-normal text-muted-foreground">uses</span>
                      </div>
                      <div className="text-[11px] font-mono text-muted-foreground flex items-center justify-between pt-1 border-t border-border/30">
                        <span>Last Latency:</span>
                        <span className="text-emerald-400 font-semibold">
                          {voiceMetrics?.lastLatencyMs?.webSpeech ? `${voiceMetrics.lastLatencyMs.webSpeech}ms` : "Real-time"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Failover Event History */}
                  <div className="space-y-2 pt-2">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span className="font-semibold uppercase text-[10px] tracking-wider flex items-center gap-1">
                        <Zap className="h-3 w-3 text-amber-400" /> Failover & Switch History
                      </span>
                      <span className="font-mono text-[10px]">
                        {voiceMetrics?.failoverEvents?.length || 0} events
                      </span>
                    </div>

                    {(!voiceMetrics?.failoverEvents || voiceMetrics.failoverEvents.length === 0) ? (
                      <div className="rounded-lg border border-border/20 bg-muted/10 p-3 text-center text-xs text-muted-foreground italic">
                        No failover events recorded yet. Providers are operating nominally.
                      </div>
                    ) : (
                      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {voiceMetrics.failoverEvents.map((ev, idx) => (
                          <div
                            key={idx}
                            className="text-xs p-2 rounded-md bg-amber-500/5 border border-amber-500/20 flex items-center justify-between gap-3"
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="text-[10px] font-mono text-muted-foreground shrink-0">{ev.timestamp}</span>
                              <span className="font-mono text-[11px] font-semibold text-amber-400 shrink-0">
                                {ev.from.toUpperCase()} → {ev.to.toUpperCase()}
                              </span>
                              <span className="text-muted-foreground truncate text-[11px]">
                                {ev.toast || ev.reason}
                              </span>
                            </div>
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 shrink-0">
                              Switched
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </div>
      </Tabs>

      {/* Input Box - Positioned absolutely at the bottom over the content (hidden on terminal/metrics to give full view) */}
      {activeCenterTab !== "terminal" && activeCenterTab !== "metrics" && (
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#0D1117] via-[#0D1117]/90 to-transparent pt-12">
        <div className="max-w-4xl mx-auto relative">
          <form onSubmit={handleSend} className="relative rounded-xl border border-border/50 bg-card shadow-2xl focus-within:ring-1 focus-within:ring-primary/50 focus-within:border-primary/50 transition-all flex flex-col">
            <div className="flex items-end p-2 gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button type="button" variant="ghost" size="icon" className="h-9 w-9 rounded-lg hover:bg-accent shrink-0 text-muted-foreground">
                    <Plus className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-56" sideOffset={8}>
                  <DropdownMenuItem className="gap-2 text-xs cursor-pointer" onSelect={(e) => {
                    e.preventDefault();
                    document.getElementById('media-upload')?.click();
                  }}>
                    <Paperclip className="h-4 w-4" />
                    Upload Media (PDF, Images, etc)
                  </DropdownMenuItem>
                  <DropdownMenuItem className="gap-2 text-xs cursor-pointer" onSelect={() => setActiveLeftTab('tools')}>
                    <Wrench className="h-4 w-4" />
                    Manage Tools
                  </DropdownMenuItem>
                  <DropdownMenuItem className="gap-2 text-xs cursor-pointer" onSelect={() => setActiveLeftTab('model')}>
                    <Cpu className="h-4 w-4" />
                    Change Model
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <input type="file" id="media-upload" className="hidden" multiple accept="image/*,application/pdf" onChange={(e) => {
                // Mock handling file upload
                if (e.target.files && e.target.files.length > 0) {
                  alert(`Selected ${e.target.files.length} file(s). Media upload will be processed by the agent.`);
                }
              }} />
              
              <div className="flex-1 flex flex-col relative min-h-[44px]">
                {cmdMenu && filteredCmdItems.length > 0 && (
                  <div className="absolute bottom-full left-0 mb-2 w-64 bg-popover border border-border shadow-md rounded-md overflow-hidden z-50">
                    <div className="px-2 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase bg-muted/50 border-b border-border/50">
                      {cmdMenu === 'model' ? 'Select Model' : 'Toggle Tool'}
                    </div>
                    <div className="max-h-48 overflow-y-auto p-1">
                      {filteredCmdItems.map((item, idx) => (
                        <div 
                          key={item.id}
                          className={`px-2 py-1.5 text-xs rounded-sm cursor-pointer flex items-center justify-between ${idx === cmdIndex ? 'bg-primary/10 text-primary' : 'hover:bg-accent hover:text-accent-foreground'}`}
                          onClick={() => handleCmdSelect(item)}
                        >
                          <div className="flex items-center gap-2">
                            {cmdMenu === 'model' ? <Cpu className="h-3.5 w-3.5" /> : <Wrench className="h-3.5 w-3.5" />}
                            <span>{item.name}</span>
                          </div>
                          {cmdMenu === 'tool' && activeTools.includes(item.id) && (
                            <div className="h-2 w-2 rounded-full bg-emerald-500" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                  <textarea
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={(e) => {
                    if (cmdMenu && filteredCmdItems.length > 0) {
                      if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        setCmdIndex(prev => (prev + 1) % filteredCmdItems.length);
                        return;
                      }
                      if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        setCmdIndex(prev => (prev - 1 + filteredCmdItems.length) % filteredCmdItems.length);
                        return;
                      }
                      if (e.key === 'Enter' || e.key === 'Tab') {
                        e.preventDefault();
                        handleCmdSelect(filteredCmdItems[cmdIndex]);
                        return;
                      }
                      if (e.key === 'Escape') {
                        e.preventDefault();
                        setCmdMenu(null);
                        return;
                      }
                    }
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend(e);
                    }
                  }}
                  placeholder="Ask the agent to build, debug, or analyze..."
                  className="w-full resize-none bg-transparent py-3 text-sm focus:outline-none placeholder:text-muted-foreground/70"
                  rows={1}
                />
              </div>

              <Button
                type="button"
                onClick={toggleListening}
                disabled={isThinking}
                variant="ghost"
                size="icon"
                className={`h-9 w-9 rounded-lg shrink-0 mb-1 transition-all ${
                  isListening
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/50 animate-pulse shadow-sm shadow-rose-500/20"
                    : isTranscribing
                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/50"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                }`}
                title={
                  isListening
                    ? "Listening (Click to finish speech typing)..."
                    : isTranscribing
                    ? "Transcribing voice audio..."
                    : "Voice Typing (Web Speech API / Groq Whisper 3-provider fallback)"
                }
                aria-label="Voice Typing"
              >
                {isTranscribing ? (
                  <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                ) : isListening ? (
                  <Mic className="h-4 w-4 text-rose-400 animate-bounce" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>

              <Button 
                type="submit" 
                disabled={!input.trim() || isThinking}
                className="h-9 w-9 rounded-lg shrink-0 bg-[#22D3EE] text-black hover:bg-[#22D3EE]/90 shadow-none mb-1 mr-1 disabled:opacity-50"
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="px-3 pb-2 pt-0 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground bg-accent/30 px-1.5 py-0.5 rounded flex items-center gap-1 border border-border/50">
                  <Cpu className="h-3 w-3" />
                  {getModelName(model)}
                </span>
              </div>
              <span className="text-[9px] text-muted-foreground/70 hidden sm:inline">
                AI Engineering Workspace uses advanced models. Verify generated code.
              </span>
            </div>
          </form>
        </div>
      </div>
      )}
    </div>
  );
}
