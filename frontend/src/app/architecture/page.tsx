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
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
              System Architecture
            </h1>
            <p className="mt-4 text-xl text-muted-foreground">
              A highly parallelized agent topology integrated with vector search databases and live telemetry log systems.
            </p>
          </div>

          {/* Architecture Blocks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
            <div className="rounded-xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Network className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold mb-3">Multi-Agent Orchestrator</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Uses a decoupled Supervisor-Worker configuration. The planner agent decomposes user objectives into logical verification phases, dispatching specific subtasks to execute, test, and reflect agents.
              </p>
            </div>

            <div className="rounded-xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Database className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold mb-3">Knowledge Graph RAG</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Indexes code hierarchies, dependency graphs, and workspace configurations in Neo4j databases combined with semantic vector embeddings in Qdrant collections.
              </p>
            </div>

            <div className="rounded-xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Compass className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold mb-3">Knowledge Sync Engine</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Incrementally crawls Git repository updates, documentation directories, and local configurations. Uses file checksum hashes to prevent redundant model embedding updates.
              </p>
            </div>

            <div className="rounded-xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Eye className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold mb-3">Structured Telemetry</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Every single agent call, prompt invocation, token dispatch, and shell execution is tracked via structured JSON streams, aggregated into live dashboard metrics.
              </p>
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
