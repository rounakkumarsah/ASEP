"use client";

import * as React from "react";
import { Settings2, Cpu, Shield, Database, Globe, PanelLeftClose, Server, ChevronRight } from "lucide-react";
import { GitHubIcon } from "@/components/icons/GitHubIcon";
import dynamic from "next/dynamic";
const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import { useSidebarStore } from "@/lib/stores/sidebarStore";

export function LeftPanel() {
  const {
    model, setModel,
    temperature, setTemperature,
    maxTokens, setMaxTokens,
    systemPrompt, setSystemPrompt,
    activeTools, toggleTool,
    researchMode, setResearchMode,
    activeLeftTab, setActiveLeftTab,
  } = usePlaygroundStore();
  const { toggleLeftPanel } = useSidebarStore();

  const [isPromptLoading, setIsPromptLoading] = React.useState(false);
  const [promptError, setPromptError] = React.useState(false);

  const fetchPrompt = React.useCallback(async () => {
    setIsPromptLoading(true);
    setPromptError(false);
    const controller = new AbortController();
    try {
      const apiBase = "";
      const timeoutId = setTimeout(() => controller.abort(), 8000);
      const res = await fetch(`${apiBase}/api/v1/prompts/system`, {
        signal: controller.signal,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('asep_auth_token') || sessionStorage.getItem('asep_auth_token') || ''}`
        }
      });
      clearTimeout(timeoutId);
      // 404 means endpoint doesn't exist yet — silently use persisted value
      if (res.status === 404) return;
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      if (data.prompt) setSystemPrompt(data.prompt);
    } catch (err) {
      // Only show error if it wasn't an abort (timeout)
      const isTimeout = err instanceof Error && err.name === 'AbortError';
      if (!isTimeout) setPromptError(true);
    } finally {
      setIsPromptLoading(false);
    }
  }, [setSystemPrompt]);

  React.useEffect(() => {
    fetchPrompt();
  }, [fetchPrompt]);

  interface MCPToolItem {
    name: string;
    description: string;
    server: string;
    inputSchema?: Record<string, unknown>;
  }
  const [mcpTools, setMcpTools] = React.useState<MCPToolItem[]>([]);
  const [isMcpLoading, setIsMcpLoading] = React.useState(false);
  const [expandedSchemas, setExpandedSchemas] = React.useState<Record<string, boolean>>({});

  const fetchMcpTools = React.useCallback(async () => {
    setIsMcpLoading(true);
    try {
      const apiBase = "";
      const res = await fetch(`${apiBase}/api/v1/mcp/tools`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('asep_auth_token') || sessionStorage.getItem('asep_auth_token') || ''}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.tools) {
          setMcpTools(data.tools);
        }
      }
    } catch {
      // ignore
    } finally {
      setIsMcpLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchMcpTools();
  }, [fetchMcpTools]);

  return (
    <div className="flex h-full flex-col border-r border-border/40 bg-background/50 backdrop-blur">
      <div className="p-4 pb-2 border-b border-border/40 flex items-center justify-between">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Settings2 className="h-4 w-4 text-primary" />
          Configuration
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleLeftPanel}
          className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
          title="Collapse Configuration Panel (Ctrl+[)"
          aria-label="Collapse Configuration Panel"
        >
          <PanelLeftClose className="h-4 w-4" />
        </Button>
      </div>

      <Tabs value={activeLeftTab} onValueChange={setActiveLeftTab} className="flex-1 flex flex-col min-h-0">
        <div className="px-4 py-2 border-b border-border/40">
          <TabsList className="w-full grid grid-cols-3 h-8 bg-muted/50 p-0.5">
            <TabsTrigger value="model" className="text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm">Model</TabsTrigger>
            <TabsTrigger value="prompt" className="text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm">Prompt</TabsTrigger>
            <TabsTrigger value="tools" className="text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm">Tools</TabsTrigger>
          </TabsList>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4">
            <TabsContent value="model" className="mt-0 space-y-6 data-[state=active]:block data-[state=inactive]:hidden">
              <div className="space-y-3">
                <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Router</Label>
                <Select value={model} onValueChange={setModel}>
                  <SelectTrigger className="h-9 bg-accent/20 border-border/50">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gemini-flash-latest">Gemini 1.5 Flash</SelectItem>
                    <SelectItem value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet</SelectItem>
                    <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                    <SelectItem value="deepseek-coder">DeepSeek Coder V2</SelectItem>
                    <SelectItem value="auto-router">Auto Router (Cost/Perf)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between">
                  <Label className="text-xs">Temperature</Label>
                  <span className="text-xs text-muted-foreground font-mono">{temperature}</span>
                </div>
                <Slider
                  value={[temperature]}
                  max={2}
                  step={0.1}
                  onValueChange={(v) => setTemperature(v[0])}
                  className="[&_[role=slider]]:h-3 [&_[role=slider]]:w-3"
                />
              </div>

              <div className="space-y-4">
                <div className="flex justify-between">
                  <Label className="text-xs">Max Tokens</Label>
                  <span className="text-xs text-muted-foreground font-mono">{maxTokens}</span>
                </div>
                <Slider
                  value={[maxTokens]}
                  max={8192}
                  step={256}
                  onValueChange={(v) => setMaxTokens(v[0])}
                  className="[&_[role=slider]]:h-3 [&_[role=slider]]:w-3"
                />
              </div>
            </TabsContent>

            <TabsContent value="prompt" className="mt-0 h-[400px] flex-col space-y-3 data-[state=active]:flex data-[state=inactive]:hidden">
              <div className="flex justify-between items-center">
                <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">System Instructions</Label>
                <div className="flex gap-2 items-center">
                  {isPromptLoading && <span className="text-[10px] text-muted-foreground animate-pulse">Syncing...</span>}
                  {promptError && (
                    <Button variant="outline" size="sm" onClick={fetchPrompt} className="h-6 text-[10px] px-2 text-destructive border-destructive/50 hover:bg-destructive/10">
                      Retry Sync
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" className="h-6 text-[10px] px-2 text-primary hover:bg-primary/10">Optimize</Button>
                  <Button variant="ghost" size="sm" className="h-6 text-[10px] px-2 text-muted-foreground">Reset</Button>
                </div>
              </div>
              <div className="flex-1 rounded-md overflow-hidden border border-border/50 bg-background/50 relative">
                <Editor
                  height="100%"
                  defaultLanguage="markdown"
                  theme="vs-dark"
                  value={systemPrompt}
                  onChange={(v) => setSystemPrompt(v || "")}
                  loading={<div className="absolute inset-0 p-4 space-y-2"><div className="h-3 bg-muted/20 rounded w-1/2 animate-pulse" /><div className="h-3 bg-muted/20 rounded w-3/4 animate-pulse" /></div>}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 12,
                    lineNumbers: "on",
                    scrollBeyondLastLine: false,
                    wordWrap: "on",
                    padding: { top: 12, bottom: 12 },
                  }}
                />
              </div>
            </TabsContent>

            <TabsContent value="tools" className="mt-0 space-y-6 data-[state=active]:block data-[state=inactive]:hidden">
              <div className="space-y-4">
                <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Available Tools</Label>
                <div className="space-y-3">
                  {[
                    { id: "web", icon: Globe, label: "Web Search" },
                    { id: "docs", icon: Database, label: "Official Docs" },
                    { id: "github", icon: GitHubIcon, label: "GitHub Repos" },
                    { id: "python", icon: Cpu, label: "Python Sandbox" },
                  ].map((t) => (
                    <div key={t.id} className="flex items-center space-x-3">
                      <Checkbox
                        id={`tool-${t.id}`}
                        checked={activeTools.includes(t.id)}
                        onCheckedChange={() => toggleTool(t.id)}
                      />
                      <Label htmlFor={`tool-${t.id}`} className="flex items-center gap-2 text-xs font-medium cursor-pointer">
                        <t.icon className="h-3.5 w-3.5 text-muted-foreground" />
                        {t.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="h-px bg-border/40" />

              {/* MCP Tools Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Server className="h-3.5 w-3.5 text-primary" />
                    MCP Tools
                  </Label>
                  <span className="text-[10px] text-muted-foreground font-mono bg-muted/40 px-1.5 py-0.5 rounded">
                    {mcpTools.length} connected
                  </span>
                </div>

                {isMcpLoading && mcpTools.length === 0 ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-8 rounded bg-muted/20 animate-pulse" />
                    ))}
                  </div>
                ) : mcpTools.length === 0 ? (
                  <div className="p-3 border border-dashed border-border/50 rounded-lg text-center text-xs text-muted-foreground space-y-1">
                    <p>No MCP tools connected.</p>
                    <a href="/settings?tab=mcp" className="text-primary hover:underline font-medium text-[11px] inline-block">
                      Configure MCP Servers &rarr;
                    </a>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {mcpTools.map((t) => {
                      const isExpanded = Boolean(expandedSchemas[t.name]);
                      const isChecked = activeTools.includes(t.name) || !activeTools.length;
                      return (
                        <div
                          key={t.name}
                          className="p-2 rounded-lg border border-border/40 bg-background/40 space-y-1 text-xs hover:border-border/70 transition-colors"
                        >
                          <div className="flex items-center justify-between gap-1">
                            <div className="flex items-center space-x-2 truncate">
                              <Checkbox
                                id={`mcp-tool-${t.name}`}
                                checked={isChecked}
                                onCheckedChange={() => toggleTool(t.name)}
                              />
                              <Label
                                htmlFor={`mcp-tool-${t.name}`}
                                className="font-mono text-[11px] font-semibold truncate cursor-pointer hover:text-foreground"
                              >
                                {t.name}
                              </Label>
                            </div>
                            <Badge
                              variant="outline"
                              className="text-[9px] border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shrink-0 font-medium px-1.5 py-0"
                            >
                              via MCP: {t.server}
                            </Badge>
                          </div>
                          <p className="text-[11px] text-muted-foreground line-clamp-2 pl-6">
                            {t.description}
                          </p>

                          {t.inputSchema && Object.keys(t.inputSchema).length > 0 && (
                            <div className="pl-6 pt-0.5">
                              <button
                                type="button"
                                onClick={() =>
                                  setExpandedSchemas((prev) => ({
                                    ...prev,
                                    [t.name]: !prev[t.name],
                                  }))
                                }
                                className="text-[10px] text-muted-foreground/80 hover:text-foreground flex items-center gap-1 font-mono transition-colors"
                              >
                                <ChevronRight
                                  className={`h-2.5 w-2.5 transition-transform ${
                                    isExpanded ? "rotate-90 text-primary" : ""
                                  }`}
                                />
                                {isExpanded ? "Hide Schema" : "View Schema"}
                              </button>
                              {isExpanded && (
                                <pre className="mt-1 p-1.5 rounded bg-muted/30 border border-border/30 text-[9px] font-mono text-muted-foreground overflow-x-auto max-h-28">
                                  {JSON.stringify(t.inputSchema, null, 2)}
                                </pre>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="h-px bg-border/40" />

              <div className="space-y-4">
                <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <Shield className="h-3 w-3" />
                  Research Mode
                </Label>
                <RadioGroup value={researchMode} onValueChange={setResearchMode} className="space-y-2">
                  {[
                    { id: "off", label: "Off (Fast)" },
                    { id: "balanced", label: "Balanced" },
                    { id: "deep", label: "Deep Research" },
                    { id: "security", label: "Security Audit" },
                  ].map((r) => (
                    <div key={r.id} className="flex items-center space-x-3">
                      <RadioGroupItem value={r.id} id={`mode-${r.id}`} />
                      <Label htmlFor={`mode-${r.id}`} className="text-xs cursor-pointer">{r.label}</Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            </TabsContent>
          </div>
        </ScrollArea>
      </Tabs>
    </div>
  );
}
