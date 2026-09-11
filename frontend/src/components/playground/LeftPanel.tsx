"use client";

import * as React from "react";
import { Settings2, Cpu, Wrench, Shield, Database, Globe, Github } from "lucide-react";
import Editor from "@monaco-editor/react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Button } from "@/components/ui/button";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";

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

  return (
    <div className="flex h-full flex-col border-r border-border/40 bg-background/50 backdrop-blur">
      <div className="p-4 pb-2 border-b border-border/40">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Settings2 className="h-4 w-4 text-primary" />
          Configuration
        </h2>
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
            <TabsContent value="model" className="mt-0 space-y-6">
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

            <TabsContent value="prompt" className="mt-0 h-[400px] flex flex-col space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">System Instructions</Label>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" className="h-6 text-[10px] px-2 text-primary hover:bg-primary/10">Optimize</Button>
                  <Button variant="ghost" size="sm" className="h-6 text-[10px] px-2 text-muted-foreground">Reset</Button>
                </div>
              </div>
              <div className="flex-1 rounded-md overflow-hidden border border-border/50 bg-background/50">
                <Editor
                  height="100%"
                  defaultLanguage="markdown"
                  theme="vs-dark"
                  value={systemPrompt}
                  onChange={(v) => setSystemPrompt(v || "")}
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

            <TabsContent value="tools" className="mt-0 space-y-6">
              <div className="space-y-4">
                <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Available Tools</Label>
                <div className="space-y-3">
                  {[
                    { id: "web", icon: Globe, label: "Web Search" },
                    { id: "docs", icon: Database, label: "Official Docs" },
                    { id: "github", icon: Github, label: "GitHub Repos" },
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
