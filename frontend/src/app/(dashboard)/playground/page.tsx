"use client";

import * as React from "react";
import { Send, Terminal, RefreshCw, Bot, User as UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export default function PlaygroundPage() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  
  // Settings
  const [model, setModel] = React.useState("gemini-2.5-pro");
  const [temperature, setTemperature] = React.useState("0.7");
  const [maxTokens, setMaxTokens] = React.useState("2048");

  const templates = [
    { name: "Code Review", prompt: "Perform a security code audit on this controller:" },
    { name: "SQL Optimization", prompt: "Rewrite this subquery into a high-performance JOIN sequence:" },
    { name: "Unit Test Writer", prompt: "Write comprehensive pytest functions for this FastAPI route:" }
  ];

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const userText = input;
    const userMsg: Message = {
      role: "user",
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      // Call production AI Runtime API endpoint
      const res = await apiClient.post("/api/v1/ai-runtime/chat/completions", {
        model,
        messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens, 10),
      });

      const replyContent = res.data?.choices?.[0]?.message?.content || res.data?.content || "Model executed successfully.";

      const assistantMsg: Message = {
        role: "assistant",
        content: replyContent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errDetail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      const assistantMsg: Message = {
        role: "assistant",
        content: `Error: ${errDetail || (err as Error).message || "Failed to execute AI completion request."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, assistantMsg]);
    } finally {
      setSending(false);
    }
  };

  const applyTemplate = (prompt: string) => {
    setInput(prompt);
  };

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agent Playground</h1>
          <p className="text-muted-foreground mt-1">
            Interact directly with models, test prompt templates, and analyze sandbox behavior logs.
          </p>
        </div>
      </div>

      {messages.length === 0 ? (
        <div className="border border-dashed border-border/60 bg-card/20 p-12 text-center flex flex-col items-center justify-center rounded-xl min-h-[400px]">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
            <Terminal className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-foreground">Start your first conversation</h3>
          <p className="text-sm mt-2 mb-6 text-muted-foreground max-w-sm">
            Interactive model sandbox environment allowing real-time prompt execution testing against connected AI runtime providers.
          </p>
          <div className="flex flex-wrap justify-center gap-2 max-w-lg mb-6">
            {templates.map(t => (
              <Button 
                key={t.name} 
                variant="outline" 
                size="sm"
                onClick={() => applyTemplate(t.prompt)}
                className="text-xs"
              >
                {t.name}
              </Button>
            ))}
          </div>
          <form onSubmit={handleSend} className="w-full max-w-md flex gap-2">
            <Input
              placeholder="Ask the AI model a coding question..."
              value={input}
              onChange={e => setInput(e.target.value)}
              className="bg-card/40"
            />
            <Button type="submit" className="gap-2">
              <Send className="h-4 w-4" />
              Send
            </Button>
          </form>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[600px]">
          {/* Left Column: Settings */}
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
                    <option value="gemini-2.5-pro">Google Gemini 2.5 Pro</option>
                    <option value="claude-3-5-sonnet">Anthropic Claude 3.5 Sonnet</option>
                    <option value="gpt-4o">OpenAI GPT-4o</option>
                    <option value="deepseek-r1">OpenRouter (DeepSeek R1)</option>
                    <option value="llama-3.3-70b">Groq (Llama 3.3 70B)</option>
                    <option value="command-r-plus">Cohere Command R+</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Temperature ({temperature})</label>
                  <input 
                    type="range" 
                    min="0" 
                    max="1" 
                    step="0.1" 
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    className="w-full"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-foreground">Max Tokens</label>
                  <Input 
                    type="number"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(e.target.value)}
                    className="text-sm bg-background"
                  />
                </div>
              </div>
            </div>

            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setMessages([])} 
              className="mt-auto text-xs"
            >
              Clear Conversation
            </Button>
          </div>

          {/* Right Column: Chat Stream */}
          <div className="lg:col-span-3 border border-border/40 bg-card/30 rounded-xl p-4 flex flex-col justify-between overflow-hidden">
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {messages.map((m, idx) => (
                <div 
                  key={idx} 
                  className={`p-3 rounded-lg flex flex-col gap-1 text-sm ${
                    m.role === "user" ? "bg-primary/10 border border-primary/20 ml-8" : "bg-card border border-border/50 mr-8"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
                    <span className="flex items-center gap-1">
                      {m.role === "user" ? <UserIcon className="h-3.5 w-3.5 text-primary" /> : <Bot className="h-3.5 w-3.5 text-primary" />}
                      {m.role === "user" ? "You" : "AI Assistant"}
                    </span>
                    <span>{m.timestamp}</span>
                  </div>
                  <div className="whitespace-pre-wrap font-mono text-xs">{m.content}</div>
                </div>
              ))}
            </div>

            <form onSubmit={handleSend} className="flex gap-2 pt-4 border-t border-border/40">
              <Input 
                placeholder="Type your message or prompt..." 
                value={input}
                onChange={e => setInput(e.target.value)}
                disabled={sending}
                className="bg-card/40"
              />
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
