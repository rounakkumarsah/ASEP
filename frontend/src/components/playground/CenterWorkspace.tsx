"use client";

import * as React from "react";
import { Send, Plus, Terminal, Code, GitCompare, MessageSquare, Loader2, Bot, User as UserIcon } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";

export function CenterWorkspace() {
  const { messages, addMessage, activeCenterTab, setActiveCenterTab } = usePlaygroundStore();
  const [input, setInput] = React.useState("");
  const [isThinking, setIsThinking] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    addMessage({
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    });
    setInput("");
    setIsThinking(true);

    setTimeout(() => {
      addMessage({
        role: "assistant",
        content: "This is a mock response from the AI Engineering Workspace. I've analyzed your request and prepared the necessary artifacts.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
      setIsThinking(false);
    }, 1500);
  };

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  return (
    <div className="flex h-full flex-col bg-[#0D1117] relative">
      <Tabs value={activeCenterTab} onValueChange={setActiveCenterTab} className="flex-1 flex flex-col min-h-0">
        <div className="px-4 py-2 border-b border-border/40 bg-background/50 backdrop-blur">
          <TabsList className="bg-muted/50 h-9 p-1">
            <TabsTrigger value="chat" className="text-xs gap-2"><MessageSquare className="h-3.5 w-3.5" /> Chat</TabsTrigger>
            <TabsTrigger value="artifacts" className="text-xs gap-2"><Code className="h-3.5 w-3.5" /> Artifacts</TabsTrigger>
            <TabsTrigger value="diff" className="text-xs gap-2"><GitCompare className="h-3.5 w-3.5" /> Diff Viewer</TabsTrigger>
            <TabsTrigger value="terminal" className="text-xs gap-2"><Terminal className="h-3.5 w-3.5" /> Terminal</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 min-h-0 relative">
          <TabsContent value="chat" className="h-full mt-0 border-0">
            <ScrollArea className="h-full">
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
                
                {isThinking && (
                  <div className="flex gap-4 justify-start">
                    <div className="h-8 w-8 rounded bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
                      <Loader2 className="h-4 w-4 text-primary animate-spin" />
                    </div>
                    <div className="bg-card border border-border/50 rounded-xl px-4 py-3 text-sm flex items-center gap-2 text-muted-foreground shadow-sm">
                      <div className="flex gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                      Thinking...
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="artifacts" className="h-full mt-0 border-0 flex">
            <div className="w-64 border-r border-border/40 bg-background/50 p-4">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Files</h4>
              <div className="space-y-1">
                <div className="text-xs p-1.5 rounded bg-accent text-accent-foreground flex items-center gap-2 cursor-pointer font-mono">
                  <Code className="h-3 w-3 text-emerald-400" /> main.py
                </div>
                <div className="text-xs p-1.5 rounded hover:bg-accent/50 text-muted-foreground flex items-center gap-2 cursor-pointer font-mono">
                  <Code className="h-3 w-3 text-amber-400" /> config.json
                </div>
              </div>
            </div>
            <div className="flex-1 bg-[#1E1E1E]">
              <Editor
                height="100%"
                defaultLanguage="python"
                theme="vs-dark"
                value={`def calculate_metrics(data):\n    # TODO: Implement metrics calculation\n    return {"status": "success"}`}
                options={{ minimap: { enabled: false }, fontSize: 13, padding: { top: 16 } }}
              />
            </div>
          </TabsContent>

          <TabsContent value="diff" className="h-full mt-0 border-0 p-8 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <GitCompare className="h-8 w-8 mx-auto mb-3 opacity-50" />
              <p>No active diffs to show.</p>
            </div>
          </TabsContent>

          <TabsContent value="terminal" className="h-full mt-0 border-0 bg-black p-4 font-mono text-sm text-green-400">
            <div>$ agent-cli run --mode=deep</div>
            <div className="text-muted-foreground">Initializing environment...</div>
            <div>[OK] Environment ready.</div>
            <div className="animate-pulse">_</div>
          </TabsContent>
        </div>
      </Tabs>

      {/* Input Box - Positioned absolutely at the bottom over the content */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#0D1117] via-[#0D1117]/90 to-transparent pt-12">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSend} className="relative rounded-xl border border-border/50 bg-card shadow-2xl focus-within:ring-1 focus-within:ring-primary/50 focus-within:border-primary/50 transition-all">
            <div className="flex items-end p-2 gap-2">
              <Button type="button" variant="ghost" size="icon" className="h-9 w-9 rounded-lg hover:bg-accent shrink-0 text-muted-foreground">
                <Plus className="h-5 w-5" />
              </Button>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e);
                  }
                }}
                placeholder="Ask the agent to build, debug, or analyze..."
                className="min-h-[44px] max-h-[200px] w-full resize-none bg-transparent py-3 text-sm focus:outline-none placeholder:text-muted-foreground/70"
                rows={1}
              />
              <Button 
                type="submit" 
                disabled={!input.trim() || isThinking}
                className="h-9 w-9 rounded-lg shrink-0 bg-[#22D3EE] text-black hover:bg-[#22D3EE]/90 shadow-none mb-1 mr-1 disabled:opacity-50"
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </form>
          <div className="text-center mt-2">
            <span className="text-[10px] text-muted-foreground">
              AI Engineering Workspace uses advanced models. Verify generated code.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
