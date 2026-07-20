import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { Book, Code, Shield } from "lucide-react";

export const metadata: Metadata = {
  title: "Documentation | ASEP",
  description: "Read the setup guides, API schemas, config details, and platform runtime manuals for ASEP.",
  openGraph: {
    title: "Documentation - ASEP",
    description: "Read the setup guides, API schemas, config details, and platform runtime manuals for ASEP.",
    type: "website",
  },
};

export default function DocumentationPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
            {/* Sidebar nav (simplified for docs) */}
            <div className="hidden lg:block space-y-6">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase mb-3">Getting Started</h3>
                <nav className="flex flex-col space-y-2">
                  <a href="#" className="text-sm font-semibold text-primary">Overview</a>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Installation</a>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Quickstart Guide</a>
                </nav>
              </div>
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase mb-3">Core Concepts</h3>
                <nav className="flex flex-col space-y-2">
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Agent Topology</a>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Sandbox Security</a>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Memory Synchronization</a>
                </nav>
              </div>
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase mb-3">API Reference</h3>
                <nav className="flex flex-col space-y-2">
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Authentication</a>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Workspace Control</a>
                  <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Governance Webhooks</a>
                </nav>
              </div>
            </div>

            {/* Docs content */}
            <div className="lg:col-span-3 max-w-3xl">
              <h1 className="text-4xl font-extrabold tracking-tight mb-4">Documentation</h1>
              <p className="text-xl text-muted-foreground mb-8">
                Welcome to the ASEP documentation. Learn how to configure, run, and scale local agent groups safely.
              </p>

              <div className="space-y-12">
                <section>
                  <h2 className="text-2xl font-bold mb-4 flex items-center gap-3">
                    <Book className="h-6 w-6 text-primary" />
                    Introduction
                  </h2>
                  <p className="text-muted-foreground leading-relaxed">
                    ASEP provides developers and security teams with an isolated control plane to host autonomous software agents. Unlike standard cloud-based coding assistants, ASEP coordinates agents directly inside secure, local runtime sandboxes on your workspace host, connecting with standard Git and IDE toolchains under enterprise governance controls.
                  </p>
                </section>

                <section>
                  <h2 className="text-2xl font-bold mb-4 flex items-center gap-3">
                    <Code className="h-6 w-6 text-primary" />
                    Local Sandbox Setup
                  </h2>
                  <p className="text-muted-foreground leading-relaxed mb-4">
                    The platform runtime executes in Docker containers, managing distinct services for memory logging (Redis), code semantic indexing (Qdrant), structure relation (Postgres), and API servers.
                  </p>
                  <div className="bg-muted p-4 rounded-lg font-mono text-xs overflow-x-auto border border-border/50">
                    docker compose up --build -d
                  </div>
                </section>

                <section>
                  <h2 className="text-2xl font-bold mb-4 flex items-center gap-3">
                    <Shield className="h-6 w-6 text-primary" />
                    Governance & Policy Configuration
                  </h2>
                  <p className="text-muted-foreground leading-relaxed">
                    Prevent AI hallucinations from deleting resources or rewriting master branches. The built-in HITL checkpoint gate suspends executor agents when high-risk operations (e.g. force push, server shutdown) are initiated, dispatching real-time browser confirmations.
                  </p>
                </section>
              </div>
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
