"use client";

import React, { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { apiClient } from "@/lib/api/client";
import { AnimatedCard } from "@/components/ui/animated-card";

export default function ResearchPage() {
  const [topic, setTopic] = useState("");
  const [depth, setDepth] = useState("Medium");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  const handleResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setError("");
    setReport(null);

    try {
      const response = await apiClient.post("/research/topic", {
        topic: `${topic} (${depth} Research)`,
      });
      setReport(response.data as Record<string, unknown>);
    } catch (err: unknown) {
      const apiErr = err as { message?: string };
      setError(apiErr.message || "Failed to execute research swarm.");
    } finally {
      setLoading(false);
    }
  };


  const handleExportMarkdown = () => {
    if (!report) return;
    const content = `# Deep Research Report: ${String(report.topic || "")}\n\n${String(report.summary || "")}\n\nSources:\n${
      Array.isArray(report.sources) ? (report.sources as string[]).join("\n") : ""
    }`;
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `research_report_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Autonomous Deep Research Swarm</h1>
          <p className="text-sm text-zinc-400">
            Powered by Google Gemini Free API + DuckDuckGo Web Scraper.
          </p>
        </div>


        <AnimatedCard className="p-6">
          <form onSubmit={handleResearch} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Research Topic or Architecture Subject
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Microservices event-driven GraphRAG using Qdrant and Neo4j"
                className="w-full px-4 py-3 rounded-xl bg-background/50 border border-border text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary transition"
                required
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <label className="text-xs text-muted-foreground">Depth:</label>
                <select
                  value={depth}
                  onChange={(e) => setDepth(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-background/50 border border-border text-xs text-foreground focus:outline-none"
                >
                  <option value="Shallow">Shallow (Fast Summary)</option>
                  <option value="Medium">Medium (Balanced)</option>
                  <option value="Deep">Deep (Comprehensive)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading || !topic.trim()}
                className="px-6 py-2.5 rounded-xl bg-primary hover:bg-primary/90 disabled:opacity-50 text-xs font-semibold text-primary-foreground transition flex items-center space-x-2 relative z-10"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">🌀</span>
                    <span>Searching & Synthesizing...</span>
                  </>
                ) : (
                  <span>Run Research Swarm</span>
                )}
              </button>
            </div>
          </form>
        </AnimatedCard>

        {error && (
          <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-xs text-destructive">
            {error}
          </div>
        )}

        {loading && (
          <AnimatedCard className="p-8 text-center space-y-3">
            <div className="inline-block animate-spin text-3xl">🔍</div>
            <p className="text-sm font-medium text-foreground">Swarms searching DuckDuckGo & scraping web documentation...</p>
            <p className="text-xs text-muted-foreground">Enforcing Gemini 15 RPM free tier queue protection</p>
          </AnimatedCard>
        )}

        {report && (
          <AnimatedCard className="p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-border/40 pb-4">
              <div>
                <span className="text-xs text-muted-foreground">Report Topic</span>
                <h2 className="text-lg font-bold text-foreground">{String(report.topic || "")}</h2>
              </div>
              <div className="flex items-center space-x-3 relative z-10">
                <button
                  onClick={handleExportMarkdown}
                  className="px-3 py-1 rounded-lg bg-muted hover:bg-muted/80 text-xs font-semibold text-foreground transition flex items-center space-x-1"
                >
                  <span>📥 Export .md</span>
                </button>
                <span className="px-3 py-1 rounded-full text-xs font-mono bg-background border border-border text-muted-foreground">
                  {String(report.latency_ms || 0)} ms
                </span>
              </div>
            </div>

            <div className="prose prose-invert max-w-none text-sm text-foreground/80 space-y-4 whitespace-pre-line">
              {String(report.summary || "")}
            </div>

            {Array.isArray(report.sources) && report.sources.length > 0 && (
              <div className="border-t border-border/40 pt-4">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Citations & Sources
                </h3>
                <ul className="flex flex-wrap gap-2 relative z-10">
                  {(report.sources as string[]).map((src: string, idx: number) => (
                    <li key={idx}>
                      <a
                        href={src}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1 rounded-lg bg-background/50 border border-border text-xs text-primary hover:underline"
                      >
                        {src}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </AnimatedCard>
        )}
      </div>
    </AppLayout>
  );
}
