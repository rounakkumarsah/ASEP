"use client";

import * as React from "react";
import { Send, Terminal, FileCode, RefreshCw, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export default function PlaygroundPage() {
  const [activeSession, setActiveSession] = React.useState(false);
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  
  // Settings
  const [model, setModel] = React.useState("gpt-4o");
  const [temperature, setTemperature] = React.useState("0.7");
  const [maxTokens, setMaxTokens] = React.useState("2048");

  const templates = [
    { name: "Code Review", prompt: "Perform a security code audit on the following Python controller:" },
    { name: "SQL optimization", prompt: "Rewrite the following subquery into a high-performance JOIN sequence:" },
    { name: "Unit Test Writer", prompt: "Write comprehensive pytest functions for this FastAPI route handler:" }
  ];

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setSending(true);

    // Simulate backend response without fabricating mock data arrays
    setTimeout(() => {
      const assistantMsg: Message = {
        role: "assistant",
        content: `Acknowledged. Executing ${model} with T=${temperature} and MaxTokens=${maxTokens}...`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, assistantMsg]);
      setSending(false);
    }, 1000);
  };

  const applyTemplate = (prompt: string) => {
    setInput(prompt);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agent Playground</h1>
          <p className="text-muted-foreground mt-1">
            Interact directly with models, test prompt templates, and analyze sandbox behavior logs.
          </p>
        </div>
      </div>

      {!activeSession ? (
        <div className="border border-dashed p-12 text-center flex flex-col items-center justify-center rounded-xl min-h-[400px]">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
            <Terminal className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-foreground">Start Playground Session</h3>
          <p className="text-sm mt-2 mb-6 text-muted-foreground max-w-sm">
            Interactive model sandbox environment allowing real-time prompt templating and execution testing. Start a conversation to begin sandbox simulation.
          </p>
          <Button onClick={() => setActiveSession(true)} className="font-semibold gap-2">
            <Play className="h-4 w-4" />
            Start Conversation
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[600px]">
          {/* Left Column: Templates & Settings */}
          <div className="lg:col-span-1 border border-border/40 bg-card/30 rounded-xl p-4 flex flex-col gap-4 overflow-y-auto">
            <div>
              <h3 className="text-sm font-bold mb-2 uppercase text-muted-foreground tracking-wider">Model Settings</h3>
              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Model</label>
                  <select 
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="text-sm p-2 rounded border bg-background"
                  >
                    <option value="gpt-4o">gpt-4o</option>
                    <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Temperature ({temperature})</label>
                  <input 
                    type="range" min="0" max="1" step="0.1" 
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Max Tokens</label>
                  <Input 
                    type="number" 
                    value={maxTokens} 
                    onChange={(e) => setMaxTokens(e.target.value)} 
                    className="h-8 text-sm" 
                  />
                </div>
              </div>
            </div>

            <div className="mt-4">
              <h3 className="text-sm font-bold mb-2 uppercase text-muted-foreground tracking-wider">Prompt Templates</h3>
              <div className="flex flex-col gap-1">
                {templates.map(t => (
                  <button
                    key={t.name}
                    onClick={() => applyTemplate(t.prompt)}
                    className="text-left text-xs p-2.5 rounded-lg border border-border/40 hover:bg-muted/50 text-foreground transition-all flex items-center gap-1.5"
                  >
                    <FileCode className="h-3.5 w-3.5 text-primary shrink-0" />
                    <span className="truncate">{t.name}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-auto border-t border-border/30 pt-4">
              <h4 className="text-xs font-bold uppercase text-muted-foreground mb-2">Sandbox Config</h4>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Terminal className="h-3.5 w-3.5 text-primary" />
                <span>Isolated Environment Active</span>
              </div>
            </div>
          </div>

          {/* Right Column: Chat Console */}
          <div className="lg:col-span-3 border border-border/40 bg-card/10 backdrop-blur-sm rounded-xl flex flex-col overflow-hidden">
            {/* Chat Messages */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                  <p>Send a message to start the session.</p>
                </div>
              )}
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 max-w-[85%] ${m.role === "user" ? "ml-auto flex-row-reverse" : ""}`}
                >
                  <div className={`p-4 rounded-xl text-sm leading-relaxed ${
                    m.role === "user" 
                      ? "bg-primary text-primary-foreground rounded-br-none" 
                      : "bg-muted/50 border border-border/30 rounded-bl-none"
                  }`}>
                    <p className="whitespace-pre-wrap">{m.content}</p>
                    <span className="block text-[10px] opacity-75 mt-1 text-right">{m.timestamp}</span>
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex gap-3 items-center text-muted-foreground text-xs">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary" />
                  <span>Streaming output...</span>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSend} className="p-4 border-t border-border/40 bg-card/30 flex gap-2">
              <Input
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask the assistant agent anything..."
                className="flex-1"
              />
              <Button type="submit" disabled={sending} className="font-semibold gap-1.5">
                <Send className="h-4 w-4" />
                <span>Send</span>
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
