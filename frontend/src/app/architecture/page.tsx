import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { Network, Database, Compass, Eye } from "lucide-react";

export const metadata: Metadata = {
  title: "Architecture | ASEP",
  description: "Learn about the ASEP Multi-Agent orchestration, Vector Databases, Graph RAG systems, and telemetry flows.",
  openGraph: {
    title: "System Architecture - ASEP",
    description: "Learn about the ASEP Multi-Agent orchestration, Vector Databases, Graph RAG systems, and telemetry flows.",
    type: "website",
  },
};

export default function ArchitecturePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-[#F5F7FA] font-sans">
              System Architecture
            </h1>
            <p className="text-base text-[#9CA6B5] font-sans">
              A decoupled multi-agent topology integrated with vector search databases and live execution telemetry.
            </p>
          </div>

          {/* Architecture Blocks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-20">
            <div className="rounded-xl border border-[#202833] bg-[#0D1117] p-6 shadow-xs">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Network className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold mb-2 text-[#F5F7FA] font-sans">Multi-Agent Orchestrator</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Uses a decoupled Supervisor-Worker topology. The planner agent decomposes user objectives into logical verification phases, dispatching subtasks to execute, test, and reflect agents.
              </p>
            </div>

            <div className="rounded-xl border border-[#202833] bg-[#0D1117] p-6 shadow-xs">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Database className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold mb-2 text-[#F5F7FA] font-sans">Knowledge & Graph RAG</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Indexes code hierarchies, dependency graphs, and workspace configurations in Neo4j databases combined with semantic vector embeddings in Qdrant collections.
              </p>
            </div>

            <div className="rounded-xl border border-[#202833] bg-[#0D1117] p-6 shadow-xs">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Compass className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold mb-2 text-[#F5F7FA] font-sans">Knowledge Sync Engine</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Automates incremental repository indexing with real-time vector chunking, maintaining up-to-date workspace context.
              </p>
            </div>

            <div className="rounded-xl border border-[#202833] bg-[#0D1117] p-6 shadow-xs">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Eye className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold mb-2 text-[#F5F7FA] font-sans">Telemetry & Observability</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Provides end-to-end OpenTelemetry spans, audit trail logging, and performance benchmark tracking across all agent executions.
              </p>
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
