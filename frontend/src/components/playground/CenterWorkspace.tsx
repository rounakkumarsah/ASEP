"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import { MessageSquare, Code, Terminal, Send, Loader2, Bot, User as UserIcon, Plus, GitCompare, Paperclip, Wrench, Cpu, Workflow, Play, FileText, FolderGit2, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });
import ReactMarkdown from 'react-markdown';

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
  } = usePlaygroundStore();
  const [input, setInput] = React.useState("");
  const [cmdMenu, setCmdMenu] = React.useState<'tool' | 'model' | null>(null);
  const [artifactCode, setArtifactCode] = React.useState<string>("");
  const [toastMessage, setToastMessage] = React.useState<string | null>(null);
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
  const [cmdIndex, setCmdIndex] = React.useState(0);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [securityFindings, setSecurityFindings] = React.useState<any[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [editorInstance, setEditorInstance] = React.useState<any>(null);

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


  const handleResume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarificationInput.trim() || !clarificationThreadId || isThinking) return;

    addMessage({
      role: 'user',
      content: clarificationInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });

    const decision = clarificationInput;
    setClarificationInput("");
    setClarificationPrompt(null);
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
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    
    const currentInput = input;
    setInput("");
    const newThreadId = "playground-session-" + Date.now();
    setClarificationThreadId(newThreadId);
    setIsThinking(true);
    resetActiveNodes();

    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("asep_auth_token") || sessionStorage.getItem("asep_auth_token")
        : null;

      const apiBase = process.env.NEXT_PUBLIC_API_URL
        ? process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "")
        : "";
      const endpoint = `${apiBase}/api/v1/conversations/run`;

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify({
          goal: currentInput,
          thread_id: newThreadId,
          research_mode: researchMode,
          environment_mode: environmentMode,
        }),
      });

      if (!res.ok) {
        throw new Error(`API returned HTTP ${res.status}: ${res.statusText}`);
      }

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
                  // Dynamically update the active node on the visual workflow graph
                  setActiveNode(nodeName);
                  addCompletedNode(nodeName);

                  if (updateVal && typeof updateVal === "object") {
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
                          } else if (messageItem.content.includes("[MCP Confirmation Required]")) {
                            const promptText = messageItem.content.replace("[MCP Confirmation Required]", "").trim();
                            const matchTool = promptText.match(/(?:allow|tool)\s+([a-zA-Z0-9_\-\.]+)/i);
                            setMcpConfirmation({
                              tool: matchTool ? matchTool[1] : "mcp_tool",
                              message: promptText,
                            });
                          } else if (messageItem.content.includes("[MCP:")) {
                            addTerminalLog("system", messageItem.content);

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
                                usePlaygroundStore.getState().setSessionMetrics({
                                  estimatedCost: metrics.estimated_cost,
                                  confidence: metrics.confidence || null
                                });
                            } catch {}
                          } else {
                            streamMessages.push(messageItem.content);
                          }
                        } else if (messageItem.type === "tool" && messageItem.name === "github" && messageItem.content) {
                          try {
                            const parsed = JSON.parse(messageItem.content);
                            if (parsed.success && parsed.result && parsed.result.files) {
                              usePlaygroundStore.getState().setGithubRepo({
                                url: parsed.result.repo_name || "GitHub Repo",
                                files: parsed.result.files,
                                activeFile: null
                              });
                              if (parsed.result.readme) {
                                setArtifactCode(parsed.result.readme);
                              }
                            } else if (parsed.success && parsed.result && parsed.result.file && parsed.result.content) {
                              usePlaygroundStore.getState().setGithubActiveFile(parsed.result.file);
                              setArtifactCode(parsed.result.content);
                              setActiveCenterTab("artifacts");
                            }
                          } catch {
                            // ignore json parse error
                          }
                        }
                      }
                    }
                  }
                }
              }
            } catch {
              // Ignore partial JSON chunks
            }
          }
        }
      }

      if (aiResponse) {
        const codeMatch = aiResponse.match(/```(?:python|bash|sh|txt|)\n([\s\S]*?)```/);
        if (codeMatch && codeMatch[1]) {
          setArtifactCode(codeMatch[1].trim());
        }
      }

      addMessage({
        role: "assistant",
        content:
          aiResponse ||
          (streamMessages.length > 0
            ? streamMessages.join("\n\n")
            : "Task processed through LangGraph multi-agent execution pipeline."),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } catch (error) {
      console.error("LangGraph run execution error:", error);
      addMessage({
        role: "assistant",
        content: `Error executing LangGraph run: ${error instanceof Error ? error.message : "Backend unavailable"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
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
        <div className="px-4 py-2 border-b border-border/40 bg-background/50 backdrop-blur">
          <TabsList className="bg-muted/50 h-9 p-1">
            <TabsTrigger value="chat" className="text-xs gap-2"><MessageSquare className="h-3.5 w-3.5" /> Chat</TabsTrigger>
            <TabsTrigger value="workflow" className="text-xs gap-2"><Workflow className="h-3.5 w-3.5" /> Visual Workflow</TabsTrigger>
            <TabsTrigger value="artifacts" className="text-xs gap-2"><Code className="h-3.5 w-3.5" /> Artifacts</TabsTrigger>
            <TabsTrigger value="diff" className="text-xs gap-2"><GitCompare className="h-3.5 w-3.5" /> Diff Viewer</TabsTrigger>
            <TabsTrigger value="terminal" className="text-xs gap-2"><Terminal className="h-3.5 w-3.5" /> Terminal</TabsTrigger>
            {securityFindings.length > 0 && <TabsTrigger value="security" className="text-xs gap-2 text-destructive"><ShieldAlert className="h-3.5 w-3.5" /> Security Audit</TabsTrigger>}
          </TabsList>
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
                  messages.map((msg, idx) => (
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
                  ))
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
              <div className="absolute top-4 right-4 flex gap-2 z-40">
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
                  <Code className="h-4 w-4" fill="currentColor" /> Copy Code
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
            </div>
          </TabsContent>

          <TabsContent value="diff" className="flex-1 mt-0 border-0 p-8 data-[state=active]:flex data-[state=inactive]:hidden flex-col items-center justify-center text-muted-foreground min-h-0">
            <div className="text-center mb-8">
              <GitCompare className="h-8 w-8 mx-auto mb-3 opacity-50 text-emerald-500" />
              <h3 className="text-lg font-medium text-foreground">No active diffs to show</h3>
              <p className="text-sm">Run a generation task to see code changes.</p>
            </div>
            
            <div className="w-full max-w-3xl border border-border/50 rounded-lg overflow-hidden bg-background shadow-xl opacity-75">
              <div className="bg-muted px-4 py-2 border-b border-border/50 flex justify-between items-center text-xs font-mono">
                <span>Example: how changes will appear</span>
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
          </TabsContent>

          <TabsContent value="terminal" className="flex-1 mt-0 border-0 data-[state=active]:flex data-[state=inactive]:hidden min-h-0 flex-col overflow-hidden">
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
        </div>
      </Tabs>

      {/* Input Box - Positioned absolutely at the bottom over the content (hidden on terminal to give full interactive CLI) */}
      {activeCenterTab !== "terminal" && (
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
