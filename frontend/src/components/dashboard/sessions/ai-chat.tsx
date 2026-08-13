"use client";
import React, { useState } from "react";
import { Send, User, Cpu, Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export function AiChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "agent",
      content: "Hello. I am the ASEP orchestration agent. How can I help you?",
    },
    {
      id: 2,
      role: "user",
      content: "Can you review the latest PR and run security tests?",
    },
    {
      id: 3,
      role: "agent",
      content: "I have reviewed PR #42. I'm executing the 'run_security_scan' tool now...",
      status: "running",
    },
  ]);
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages([
      ...messages,
      { id: Date.now(), role: "user", content: input },
    ]);
    setInput("");
    
    // Simulate agent typing
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "agent", content: "Executing command...", status: "running" }
      ]);
    }, 500);
  };

  return (
    <div className="flex flex-col h-full bg-[#0D1117] rounded-xl border border-[#202833] overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#202833] flex justify-between items-center bg-[#111720]">
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 rounded-full bg-[#2DD4A3] animate-pulse" />
          <span className="font-mono text-sm text-[#F5F7FA] font-bold">Orchestrator Agent</span>
        </div>
        <span className="font-mono text-xs text-[#667085]">v1.0.4-stable</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex items-start gap-3 max-w-[85%]",
              msg.role === "user" ? "ml-auto flex-row-reverse" : ""
            )}
          >
            {/* Avatar */}
            <div
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border",
                msg.role === "user"
                  ? "bg-[#22D3EE]/10 border-[#22D3EE]/50 text-[#22D3EE]"
                  : "bg-[#111720] border-[#202833] text-[#9CA6B5]"
              )}
            >
              {msg.role === "user" ? <User className="h-4 w-4" /> : <Cpu className="h-4 w-4" />}
            </div>

            {/* Bubble */}
            <div
              className={cn(
                "flex flex-col gap-1 text-sm font-sans",
                msg.role === "user" ? "items-end" : "items-start"
              )}
            >
              <div
                className={cn(
                  "rounded-2xl px-4 py-2.5",
                  msg.role === "user"
                    ? "bg-[#22D3EE] text-[#090B0F] font-medium"
                    : "bg-[#111720] text-[#F5F7FA] border border-[#202833]"
                )}
              >
                {msg.content}
                {msg.status === "running" && (
                  <div className="mt-2 flex items-center space-x-2 text-[#9CA6B5] text-xs font-mono">
                    <span className="flex h-1 w-1 rounded-full bg-[#9CA6B5] animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="flex h-1 w-1 rounded-full bg-[#9CA6B5] animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="flex h-1 w-1 rounded-full bg-[#9CA6B5] animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="p-4 bg-[#111720] border-t border-[#202833]">
        <form
          onSubmit={handleSubmit}
          className="relative flex items-center bg-[#090B0F] rounded-lg border border-[#202833] shadow-inner focus-within:ring-1 focus-within:ring-[#22D3EE]/50 focus-within:border-[#22D3EE]/50 transition-all"
        >
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute left-1 text-[#667085] hover:text-[#F5F7FA]"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Instruct the agent..."
            className="w-full bg-transparent border-none focus-visible:ring-0 pl-10 pr-12 text-[#F5F7FA] font-sans placeholder:text-[#667085]"
          />
          <Button
            type="submit"
            size="icon"
            className="absolute right-1 h-8 w-8 bg-[#22D3EE] hover:bg-[#67E8F9] text-[#090B0F] rounded"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
