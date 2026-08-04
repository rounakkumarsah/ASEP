"use client";

import React, { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { apiClient } from "@/lib/api/client";

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


        <form onSubmit={handleResearch} className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
              Research Topic or Architecture Subject
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Microservices event-driven GraphRAG using Qdrant and Neo4j"
              className="w-full px-4 py-3 rounded-xl bg-zinc-950 border border-zinc-800 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500 transition"
              required
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <label className="text-xs text-zinc-400">Depth:</label>
              <select
                value={depth}
                onChange={(e) => setDepth(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-xs text-zinc-200 focus:outline-none"
              >
                <option value="Shallow">Shallow (Fast Summary)</option>
                <option value="Medium">Medium (Balanced)</option>
                <option value="Deep">Deep (Comprehensive)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading || !topic.trim()}
              className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white transition flex items-center space-x-2"
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

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/50 text-xs text-rose-300">
            {error}
          </div>
        )}

        {loading && (
          <div className="p-8 rounded-2xl bg-zinc-900/50 border border-zinc-800 text-center space-y-3">
            <div className="inline-block animate-spin text-3xl">🔍</div>
            <p className="text-sm font-medium text-zinc-300">Swarms searching DuckDuckGo & scraping web documentation...</p>
            <p className="text-xs text-zinc-500">Enforcing Gemini 15 RPM free tier queue protection</p>
          </div>
        )}

        {report && (
          <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-6">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <div>
                <span className="text-xs text-zinc-400">Report Topic</span>
                <h2 className="text-lg font-bold text-zinc-100">{String(report.topic || "")}</h2>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleExportMarkdown}
                  className="px-3 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-zinc-200 transition flex items-center space-x-1"
                >
                  <span>📥 Export .md</span>
                </button>
                <span className="px-3 py-1 rounded-full text-xs font-mono bg-zinc-950 border border-zinc-800 text-zinc-400">
                  {String(report.latency_ms || 0)} ms
                </span>
              </div>
            </div>


            <div className="prose prose-invert max-w-none text-sm text-zinc-300 space-y-4 whitespace-pre-line">
              {String(report.summary || "")}
            </div>

            {Array.isArray(report.sources) && report.sources.length > 0 && (
              <div className="border-t border-zinc-800 pt-4">
                <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                  Citations & Sources
                </h3>
                <ul className="flex flex-wrap gap-2">
                  {(report.sources as string[]).map((src: string, idx: number) => (
                    <li key={idx}>
                      <a
                        href={src}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1 rounded-lg bg-zinc-950 border border-zinc-800 text-xs text-blue-400 hover:underline"
                      >
                        {src}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}


          </div>
        )}
      </div>
    </AppLayout>
  );
}
