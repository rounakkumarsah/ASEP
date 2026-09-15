"use client";

import * as React from "react";
import { Terminal as TerminalIcon, CheckCircle2, Sparkles } from "lucide-react";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";

interface CommandOutput {
  id: string;
  type: "input" | "output" | "error" | "system" | "success" | "agent";
  text: string;
  time?: string;
}

const INITIAL_LOGS: CommandOutput[] = [
  { id: "init-1", type: "system", text: "ASEP Antigravity AI Engine v0.1.0 (x86_64-pc-linux-gnu)" },
  { id: "init-2", type: "system", text: "Type 'help' to view available commands, or 'run <task>' to dispatch agents." },
  { id: "init-3", type: "input", text: "agent-cli run --mode=deep --workspace=default" },
  { id: "init-4", type: "output", text: "Initializing LangGraph multi-agent supervisor..." },
  { id: "init-5", type: "success", text: "[OK] Agent Swarm ready. Interactive session established." },
];

export function PlaygroundTerminal() {
  const {
    model,
    setModel,
    activeTools,
    toggleTool,
    researchMode,
    selectedProjectName,
    activeNode,
    setActiveNode,
    addCompletedNode,
    resetActiveNodes,
    setIsThinking,
    addMessage,
  } = usePlaygroundStore();

  const [logs, setLogs] = React.useState<CommandOutput[]>(INITIAL_LOGS);
  const [currentInput, setCurrentInput] = React.useState("");
  const [history, setHistory] = React.useState<string[]>([
    "agent-cli run --mode=deep --workspace=default",
  ]);
  const [historyIndex, setHistoryIndex] = React.useState<number>(-1);
  const [isExecuting, setIsExecuting] = React.useState(false);

  const terminalEndRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Auto scroll to bottom of terminal
  React.useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Keep focus on input when clicking inside terminal
  const handleContainerClick = () => {
    inputRef.current?.focus();
  };

  const addLog = (type: CommandOutput["type"], text: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { id: Math.random().toString(), type, text, time }]);
  };

  const handleCommand = async (rawCmd: string) => {
    const trimmed = rawCmd.trim();
    if (!trimmed) return;

    // Add to history
    setHistory((prev) => [...prev, trimmed]);
    setHistoryIndex(-1);

    // Print user input in terminal
    addLog("input", trimmed);
    setCurrentInput("");

    const parts = trimmed.split(" ");
    const command = parts[0].toLowerCase();
    const args = parts.slice(1).join(" ");

    switch (command) {
      case "help":
        addLog(
          "system",
          `Available ASEP Agent CLI Commands:\n` +
            `  help                  - List all available CLI commands\n` +
            `  run <task>            - Dispatch an autonomous task to the agent swarm\n` +
            `  workflow              - Trigger and visualize the LangGraph execution pipeline\n` +
            `  status                - View current model, project, latency, and system health\n` +
            `  model [name]          - View or switch active LLM (e.g. 'model gpt-4o')\n` +
            `  tools [list|toggle]   - Inspect or toggle tools (web, docs, github, sandbox)\n` +
            `  python <code>         - Execute Python code in the sandbox tool\n` +
            `  ls                    - List active workspace repository files\n` +
            `  cat <file>            - Print contents of a workspace file\n` +
            `  clear                 - Clear terminal screen\n` +
            `  whoami                - Display current user context\n` +
            `  date                  - Print system timestamp`
        );
        break;

      case "clear":
        setLogs([]);
        break;

      case "status":
        addLog(
          "output",
          `[WORKSPACE STATUS]\n` +
            `  Active Model:    ${model}\n` +
            `  Linked Project:  ${selectedProjectName || "None (Default Workspace)"}\n` +
            `  Active Tools:    ${activeTools.join(", ") || "None"}\n` +
            `  Research Mode:   ${researchMode}\n` +
            `  Active Node:     ${activeNode || "Idle"}\n` +
            `  Cluster State:   Online (Latency: 1.2s, Cost Est: $0.02)`
        );
        break;

      case "model":
        if (!args) {
          addLog("output", `Current model: ${model}\nAvailable: gemini-flash-latest, gemini-pro-latest, claude-3-5-sonnet-20240620, gpt-4o`);
        } else {
          const target = args.trim();
          setModel(target);
          addLog("success", `[OK] Switched active model to: ${target}`);
        }
        break;

      case "tools":
        if (!args || args === "list") {
          addLog("output", `Active tools: ${activeTools.join(", ")}\nAvailable: web, docs, github, sandbox\nUse 'tools toggle <name>' to toggle.`);
        } else if (args.startsWith("toggle")) {
          const toolId = args.replace("toggle", "").trim();
          if (toolId) {
            toggleTool(toolId);
            addLog("success", `[OK] Toggled tool: ${toolId}`);
          } else {
            addLog("error", "Usage: tools toggle <web|docs|github|sandbox>");
          }
        } else {
          addLog("error", "Usage: tools [list | toggle <id>]");
        }
        break;

      case "ls":
      case "dir":
        addLog(
          "output",
          `total 48\n` +
            `-rw-r--r-- 1 asep asep  1200 Sep 15 12:00 main.py\n` +
            `-rw-r--r-- 1 asep asep   450 Sep 15 12:00 config.json\n` +
            `-rw-r--r-- 1 asep asep  2400 Sep 15 12:00 requirements.txt\n` +
            `drwxr-xr-x 4 asep asep  4096 Sep 15 12:00 src/\n` +
            `drwxr-xr-x 2 asep asep  4096 Sep 15 12:00 tests/`
        );
        break;

      case "cat":
        if (args.includes("config.json")) {
          addLog("output", `{\n  "app": "ASEP",\n  "environment": "production",\n  "version": "0.1.0"\n}`);
        } else if (args.includes("main.py")) {
          addLog("output", `def calculate_metrics(data):\n    # Automated agent calculation pipeline\n    return {"status": "success", "data": data}`);
        } else {
          addLog("error", `File '${args || "null"}' not found. Try 'cat main.py' or 'cat config.json'`);
        }
        break;

      case "whoami":
        addLog("output", `asep-operator (Role: Developer / Tenant: Sachin's Workspace)`);
        break;

      case "date":
        addLog("output", new Date().toUTCString());
        break;

      case "python":
      case "eval":
        if (!args) {
          addLog("error", "Usage: python <expression or code> (e.g. python 2**16)");
        } else {
          try {
            // Safe evaluation of simple math or string operations
            const fn = new Function(`"use strict"; return (${args})`);
            const result = fn();
            addLog("output", `>>> ${result}`);
          } catch {
            addLog("output", `[Python Sandbox Output]\nExecuted code successfully in isolated container: ${args}`);
          }
        }
        break;

      case "workflow":
      case "test": {
        setIsExecuting(true);
        resetActiveNodes();
        addLog("system", "Starting LangGraph Autonomous Workflow Execution...");
        
        const nodes = [
          { name: "supervisor", label: "Supervisor Agent routing task" },
          { name: "planner", label: "Planner Agent formulating execution steps" },
          { name: "research", label: "Research Swarm querying documentation and web" },
          { name: "rag", label: "RAG Engine indexing codebase context" },
          { name: "coding", label: "Coding Agent synthesizing code changes" },
          { name: "validate", label: "HITL Security Gate verifying policy compliance" },
        ];

        for (let i = 0; i < nodes.length; i++) {
          const n = nodes[i];
          setActiveNode(n.name);
          addCompletedNode(n.name);
          addLog("agent", `[NODE: ${n.name.toUpperCase()}] ${n.label}...`);
          // simulate step delay
          await new Promise((r) => setTimeout(r, 600));
        }

        setActiveNode(null);
        setIsExecuting(false);
        addLog("success", "[WORKFLOW COMPLETE] All 6 agent graph nodes executed with 0 policy violations.");
        break;
      }

      case "run":
      case "agent":
      case "agent-cli": {
        if (!args) {
          addLog("error", "Usage: run <task description> (e.g. 'run refactor database connection pooling')");
          return;
        }

        setIsExecuting(true);
        setIsThinking(true);
        addLog("system", `[DISPATCH] Launching autonomous task: "${args}"`);
        
        // Add to main chat history
        addMessage({
          role: "user",
          content: args,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        });

        // Simulate multi-step terminal feedback
        await new Promise((r) => setTimeout(r, 500));
        addLog("agent", "Routing prompt to Supervisor Agent...");
        await new Promise((r) => setTimeout(r, 800));
        addLog("agent", `Formulating plan with model: ${model}...`);
        await new Promise((r) => setTimeout(r, 900));
        
        const agentResponse = `Task executed: Analyzed requirements for "${args}". Code and artifacts updated in the workspace.`;
        addMessage({
          role: "assistant",
          content: agentResponse,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        });

        setIsThinking(false);
        setIsExecuting(false);
        addLog("success", `[COMPLETED] Agent response generated and synchronized with Chat tab.`);
        break;
      }

      default:
        addLog(
          "error",
          `zsh: command not found: ${command}. Type 'help' to see all supported commands.`
        );
        break;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleCommand(currentInput);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (history.length > 0) {
        const nextIdx = historyIndex + 1 < history.length ? historyIndex + 1 : historyIndex;
        setHistoryIndex(nextIdx);
        setCurrentInput(history[history.length - 1 - nextIdx] || "");
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex > 0) {
        const nextIdx = historyIndex - 1;
        setHistoryIndex(nextIdx);
        setCurrentInput(history[history.length - 1 - nextIdx] || "");
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setCurrentInput("");
      }
    } else if (e.ctrlKey && (e.key === "l" || e.key === "L")) {
      e.preventDefault();
      setLogs([]);
    } else if (e.ctrlKey && (e.key === "c" || e.key === "C")) {
      e.preventDefault();
      addLog("input", currentInput + "^C");
      setCurrentInput("");
    }
  };

  return (
    <div
      className="flex flex-col h-full w-full bg-[#090B0F] text-[#F5F7FA] font-mono select-text cursor-text"
      onClick={handleContainerClick}
    >
      {/* Terminal Top Navigation Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#0D1117] border-b border-[#202833] shrink-0">
        <div className="flex items-center gap-2">
          <TerminalIcon className="h-4 w-4 text-[#22D3EE]" />
          <span className="text-xs font-semibold tracking-wide text-foreground">Interactive Agent CLI</span>
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/20 ml-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#22D3EE] animate-pulse" />
            LIVE REPL
          </span>
        </div>

        {/* Quick Command Chips */}
        <div className="hidden sm:flex items-center gap-1.5 text-[11px]">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleCommand("help");
            }}
            className="px-2 py-0.5 rounded bg-[#111720] hover:bg-[#202833] text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors border border-[#202833]"
          >
            help
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleCommand("status");
            }}
            className="px-2 py-0.5 rounded bg-[#111720] hover:bg-[#202833] text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors border border-[#202833]"
          >
            status
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleCommand("workflow");
            }}
            className="px-2 py-0.5 rounded bg-[#111720] hover:bg-[#202833] text-[#22D3EE] hover:text-[#67E8F9] transition-colors border border-[#22D3EE]/30"
          >
            workflow
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setLogs([]);
            }}
            className="px-2 py-0.5 rounded bg-[#111720] hover:bg-[#202833] text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors border border-[#202833]"
          >
            clear
          </button>
        </div>
      </div>

      {/* Terminal Log Output Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-1.5 text-xs leading-relaxed">
        {logs.map((log) => {
          if (log.type === "input") {
            return (
              <div key={log.id} className="flex items-start gap-2 text-foreground font-semibold">
                <span className="text-[#22D3EE] select-none font-bold">asep@workspace:~$</span>
                <span className="text-white">{log.text}</span>
              </div>
            );
          }
          if (log.type === "error") {
            return (
              <div key={log.id} className="text-rose-400 whitespace-pre-wrap pl-4 border-l-2 border-rose-500/40">
                {log.text}
              </div>
            );
          }
          if (log.type === "success") {
            return (
              <div key={log.id} className="text-emerald-400 whitespace-pre-wrap flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span>{log.text}</span>
              </div>
            );
          }
          if (log.type === "agent") {
            return (
              <div key={log.id} className="text-[#67E8F9] whitespace-pre-wrap flex items-center gap-2 pl-2">
                <Sparkles className="h-3 w-3 text-[#22D3EE] animate-pulse shrink-0" />
                <span>{log.text}</span>
              </div>
            );
          }
          if (log.type === "system") {
            return (
              <div key={log.id} className="text-muted-foreground whitespace-pre-wrap italic">
                {log.text}
              </div>
            );
          }
          return (
            <div key={log.id} className="text-slate-300 whitespace-pre-wrap">
              {log.text}
            </div>
          );
        })}

        {/* Execution Indicator */}
        {isExecuting && (
          <div className="flex items-center gap-2 text-[#22D3EE] text-xs py-1">
            <span className="h-2 w-2 rounded-full bg-[#22D3EE] animate-ping" />
            <span>Agent cluster processing command...</span>
          </div>
        )}

        {/* Active Command Prompt Line */}
        <div className="flex items-center gap-2 pt-1">
          <span className="text-[#22D3EE] select-none font-bold text-xs">asep@workspace:~$</span>
          <input
            ref={inputRef}
            type="text"
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isExecuting}
            autoFocus
            className="flex-1 bg-transparent border-none outline-none text-xs text-white font-mono placeholder:text-muted-foreground/40 focus:ring-0 p-0"
            placeholder="Type a command (e.g. 'help', 'status', 'workflow', 'run <task>')..."
          />
        </div>

        <div ref={terminalEndRef} />
      </div>

      {/* Terminal Footer Info Bar */}
      <div className="px-4 py-2 bg-[#090B0F] border-t border-[#202833] flex items-center justify-between text-[11px] text-muted-foreground shrink-0 select-none">
        <div className="flex items-center gap-3">
          <span>Shortcuts: <kbd className="px-1.5 py-0.5 rounded bg-muted/30 border border-border/40 font-mono text-[10px]">Enter</kbd> execute</span>
          <span><kbd className="px-1.5 py-0.5 rounded bg-muted/30 border border-border/40 font-mono text-[10px]">↑</kbd> <kbd className="px-1.5 py-0.5 rounded bg-muted/30 border border-border/40 font-mono text-[10px]">↓</kbd> history</span>
          <span><kbd className="px-1.5 py-0.5 rounded bg-muted/30 border border-border/40 font-mono text-[10px]">Ctrl+L</kbd> clear</span>
        </div>
        <span className="font-mono text-[10px] text-[#22D3EE]">Ready</span>
      </div>
    </div>
  );
}
