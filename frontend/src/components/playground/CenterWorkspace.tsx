"use client";

import * as React from "react";
import { MessageSquare, Code, Terminal, Send, Loader2, Bot, User as UserIcon, Plus, GitCompare, Paperclip, Wrench, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import Editor from "@monaco-editor/react";
import ReactMarkdown from 'react-markdown';
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
  const { messages, addMessage, isThinking, activeCenterTab, setActiveCenterTab, model, setActiveLeftTab, setModel, toggleTool, activeTools } = usePlaygroundStore();
  const [input, setInput] = React.useState("");
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const [cmdMenu, setCmdMenu] = React.useState<'model' | 'tool' | null>(null);
  const [cmdFilter, setCmdFilter] = React.useState('');
  const [cmdIndex, setCmdIndex] = React.useState(0);

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

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking) return;
    
    addMessage({
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    
    setInput("");
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
      <Tabs value={activeCenterTab} onValueChange={setActiveCenterTab} className="flex-1 flex flex-col min-h-0">
        <div className="px-4 py-2 border-b border-border/40 bg-background/50 backdrop-blur">
          <TabsList className="bg-muted/50 h-9 p-1">
            <TabsTrigger value="chat" className="text-xs gap-2"><MessageSquare className="h-3.5 w-3.5" /> Chat</TabsTrigger>
            <TabsTrigger value="artifacts" className="text-xs gap-2"><Code className="h-3.5 w-3.5" /> Artifacts</TabsTrigger>
            <TabsTrigger value="diff" className="text-xs gap-2"><GitCompare className="h-3.5 w-3.5" /> Diff Viewer</TabsTrigger>
            <TabsTrigger value="terminal" className="text-xs gap-2"><Terminal className="h-3.5 w-3.5" /> Terminal</TabsTrigger>
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

          <TabsContent value="artifacts" className="flex-1 mt-0 border-0 data-[state=active]:flex data-[state=inactive]:hidden min-h-0">
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

          <TabsContent value="diff" className="flex-1 mt-0 border-0 p-8 data-[state=active]:flex data-[state=inactive]:hidden items-center justify-center text-muted-foreground min-h-0">
            <div className="text-center">
              <GitCompare className="h-8 w-8 mx-auto mb-3 opacity-50" />
              <p>No active diffs to show.</p>
            </div>
          </TabsContent>

          <TabsContent value="terminal" className="flex-1 mt-0 border-0 bg-black p-4 font-mono text-sm text-green-400 data-[state=active]:block data-[state=inactive]:hidden min-h-0 overflow-y-auto">
            <div>$ agent-cli run --mode=deep</div>
            <div className="text-muted-foreground">Initializing environment...</div>
            <div>[OK] Environment ready.</div>
            <div className="animate-pulse">_</div>
          </TabsContent>
        </div>
      </Tabs>

      {/* Input Box - Positioned absolutely at the bottom over the content */}
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
    </div>
  );
}
