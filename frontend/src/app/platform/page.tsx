import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { Cpu, Shield, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Platform | ASEP",
  description: "Explore the Autonomous Software Engineering Platform features, core execution layer, and secure agent sandboxes.",
  openGraph: {
    title: "Platform Features - ASEP",
    description: "Explore the Autonomous Software Engineering Platform features, core execution layer, and secure agent sandboxes.",
    type: "website",
  },
};

export default function PlatformPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
              The ASEP Platform
            </h1>
            <p className="mt-4 text-xl text-muted-foreground">
              Production-grade execution runtime and workspace environments designed specifically for autonomous AI engineering.
            </p>
          </div>

          {/* Core Blocks */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
            <div className="rounded-xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Cpu className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold mb-3">Agent Runtime Sandbox</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Secure, isolated sandboxes designed to execute complex shell commands, git workflows, and local software builds safely under strict resource limitations.
              </p>
            </div>

            <div className="rounded-xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Layers className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold mb-3">Multi-Agent Orchestrator</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Coordinate specialized planner, executor, and governance agents with defined handoffs, memory contexts, and structured collaboration pathways.
              </p>
            </div>

            <div className="rounded-xl border border-border/50 bg-card p-8 shadow-sm">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Shield className="h-6 w-6" />
              </div>
              <h2 className="text-xl font-bold mb-3">Enterprise Governance</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Real-time policy auditing, human-in-the-loop validation checkpoints, and precise token budget caps to prevent runaway executions.
              </p>
            </div>
          </div>

          {/* Details Section */}
          <div className="border border-border/50 rounded-2xl bg-card/50 overflow-hidden mb-20 p-8 sm:p-12">
            <div className="max-w-3xl">
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">
                Designed for Absolute Engineering Control
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-6">
                ASEP doesn&apos;t write scripts. It installs dependencies, verifies build compilation, runs pytest/vitest tests, resolves compilation errors, and manages Git commits and pushes completely autonomously. If a build fails, the platform reflector agent captures stdout/stderr and fixes it.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link href="/login">
                  <Button className="font-semibold">Launch Control Plane</Button>
                </Link>
                <Link href="/architecture">
                  <Button variant="outline" className="font-semibold">Explore System Architecture</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
