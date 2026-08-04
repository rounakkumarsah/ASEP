import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import Link from "next/link";
import { Key, FolderGit, Workflow } from "lucide-react";

export const metadata: Metadata = {
  title: "API Reference | ASEP",
  description: "Explore the ASEP Platform API schemas, endpoints, and governance webhook payloads.",
};

export default function ApiDocsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />

      <main className="flex-1 pt-32 pb-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Breadcrumb */}
          <nav className="mb-8 flex items-center space-x-2 text-sm text-muted-foreground" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
            <span>/</span>
            <span className="text-foreground font-medium">API Reference</span>
          </nav>

          <div className="max-w-4xl">
            <div className="border-b border-border/30 pb-8 mb-12">
              <h1 className="text-4xl font-extrabold tracking-tight mb-4 lg:text-5xl bg-gradient-to-r from-foreground via-foreground/90 to-muted-foreground bg-clip-text text-transparent">
                API Reference
              </h1>
              <p className="text-lg sm:text-xl text-muted-foreground leading-relaxed">
                Connect and manage your isolated local runtime sandboxes and multi-agent topology programmatically.
              </p>
            </div>

            <div className="space-y-16">
              {/* Authentication */}
              <section className="scroll-mt-36" id="auth">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-3">
                  <Key className="h-6 w-6 text-primary" />
                  Authentication & Security
                </h2>
                <p className="text-muted-foreground leading-relaxed mb-4">
                  All HTTP requests to the ASEP API must be authenticated using bearer JWT tokens or secure API keys passed in the headers. JWT tokens are issued upon successful authentication at the <code className="text-xs bg-muted px-1.5 py-0.5 rounded">/api/v1/auth/login</code> endpoint.
                </p>
                <div className="bg-muted p-4 rounded-lg font-mono text-xs overflow-x-auto border border-border/50">
                  Authorization: Bearer &lt;YOUR_JWT_ACCESS_TOKEN&gt;
                </div>
              </section>

              {/* Workspace API */}
              <section className="scroll-mt-36" id="workspace">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-3">
                  <FolderGit className="h-6 w-6 text-primary" />
                  Workspace Operations
                </h2>
                <p className="text-muted-foreground leading-relaxed mb-4">
                  Manage the local workspace volumes and host configurations that agents are permitted to mount.
                </p>
                <div className="space-y-4">
                  <div className="border border-border/40 rounded-lg p-4 bg-card/50">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="bg-green-500/10 text-green-500 text-xs font-bold px-2 py-0.5 rounded">GET</span>
                      <code className="text-sm font-semibold">/api/v1/workspace</code>
                    </div>
                    <p className="text-xs text-muted-foreground">List all configured workspace mount paths and active container details.</p>
                  </div>

                  <div className="border border-border/40 rounded-lg p-4 bg-card/50">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="bg-blue-500/10 text-blue-500 text-xs font-bold px-2 py-0.5 rounded">POST</span>
                      <code className="text-sm font-semibold">/api/v1/workspace</code>
                    </div>
                    <p className="text-xs text-muted-foreground">Configure and mount a new local repository path into the execution container.</p>
                  </div>
                </div>
              </section>

              {/* Webhooks API */}
              <section className="scroll-mt-36" id="webhooks">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-3">
                  <Workflow className="h-6 w-6 text-primary" />
                  Governance Webhooks
                </h2>
                <p className="text-muted-foreground leading-relaxed mb-4">
                  Register webhooks to receive real-time notifications about platform events, including agent execution updates and Human-in-the-Loop checkpoints.
                </p>
                <div className="border border-border/40 rounded-lg p-4 bg-card/50">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="bg-blue-500/10 text-blue-500 text-xs font-bold px-2 py-0.5 rounded">POST</span>
                    <code className="text-sm font-semibold">/api/v1/governance/webhooks</code>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">Register a new webhook listener destination URL.</p>
                  <div className="bg-muted p-3 rounded font-mono text-xs text-muted-foreground border border-border/30">
                    {JSON.stringify({
                      url: "https://yourserver.com/webhooks/asep",
                      events: ["agent.task_started", "agent.hitl_checkpoint"],
                      secret: "whsec_..."
                    }, null, 2)}
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
