"use client";

import React, { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { apiClient } from "@/lib/api/client";

export default function CopilotPage() {
  const [errorText, setErrorText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const sampleTemplates = [
    {
      label: "TypeError",
      text: "TypeError: Cannot read properties of undefined (reading 'valid_key')\n    at Object.processData (main.js:42:15)\n    at Runner.execute (runner.js:108:8)",
    },
    {
      label: "NullPointer",
      text: "java.lang.NullPointerException: Cannot invoke \"String.toLowerCase()\" because \"user.email\" is null\n\tat com.asep.service.UserService.getUserDomain(UserService.java:87)",
    },
    {
      label: "Async Timeout",
      text: "TimeoutError: Task <Task pending name='Task-4' coro=<fetch_db()>> did not complete within 10.0 seconds\n    File 'asyncio/tasks.py', line 450, in wait_for",
    },
  ];

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };


  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
    }
  };

  const handleSolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!errorText.trim() && !file) return;

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    if (errorText) formData.append("error_text", errorText);
    if (file) formData.append("image_file", file);

    try {
      const response = await apiClient.post("/research/code_issue", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data as Record<string, unknown>);
    } catch (err: unknown) {
      const apiErr = err as { message?: string };
      setError(apiErr.message || "Failed to execute copilot diagnostic.");
    } finally {
      setLoading(false);
    }
  };


  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Multimodal Developer Copilot Swarm</h1>
          <p className="text-sm text-zinc-400">
            Paste error log / code or upload a screenshot of your code traceback.
          </p>
        </div>

        <form onSubmit={handleSolve} className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                Paste Code Snippet or Error Traceback
              </label>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] text-zinc-500 font-medium">Quick Templates:</span>
                {sampleTemplates.map((tmpl) => (
                  <button
                    key={tmpl.label}
                    type="button"
                    onClick={() => setErrorText(tmpl.text)}
                    className="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-[10px] font-mono text-zinc-300 transition"
                  >
                    {tmpl.label}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              rows={4}
              value={errorText}
              onChange={(e) => setErrorText(e.target.value)}
              placeholder="TypeError: Cannot read properties of undefined (reading 'valid_key')"
              className="w-full p-4 rounded-xl bg-zinc-950 border border-zinc-800 font-mono text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
              Or Upload Screenshot (PNG, JPG)
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="text-xs text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 transition"
              />
              {preview && (
                <div className="h-12 w-12 rounded-lg border border-zinc-700 overflow-hidden relative">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={preview} alt="Screenshot preview" className="object-cover h-full w-full" />
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading || (!errorText.trim() && !file)}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-xs font-semibold text-white transition flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <span className="animate-spin">🤖</span>
                  <span>Extracting & Fixing...</span>
                </>
              ) : (
                <span>Solve Code Issue</span>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/50 text-xs text-rose-300">
            {error}
          </div>
        )}

        {result && (
          <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 space-y-6">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <div>
                <span className="text-xs text-zinc-400">Diagnostic Status</span>
                <h2 className="text-lg font-bold text-emerald-400">
                  {result.cached ? "⚡ Semantic Cache Hit" : "🔍 Swarm Diagnostic Complete"}
                </h2>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-mono bg-zinc-950 border border-zinc-800 text-zinc-400">
                {String(result.latency_ms || 0)} ms
              </span>
            </div>

            <div className="prose prose-invert max-w-none text-sm text-zinc-300 space-y-4 whitespace-pre-line">
              {String(result.diagnostic_summary || "")}
            </div>

            {Boolean(result.code_solution) && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                    Corrected Code Solution
                  </h3>
                  <button
                    onClick={() => handleCopyCode(String(result.code_solution))}
                    className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-emerald-400 transition flex items-center space-x-1"
                  >
                    <span>{copied ? "✓ Copied!" : "📋 Copy Code"}</span>
                  </button>
                </div>
                <pre className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 font-mono text-xs text-emerald-300 overflow-x-auto">
                  <code>{String(result.code_solution)}</code>
                </pre>
              </div>
            )}
          </div>
        )}

      </div>
    </AppLayout>
  );
}

