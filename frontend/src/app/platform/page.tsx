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
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-[#F5F7FA] font-sans">
              The ASEP Platform
            </h1>
            <p className="text-base text-[#9CA6B5] font-sans">
              Production-grade execution runtime and workspace environments engineered for autonomous AI software engineering.
            </p>
          </div>

          {/* Core Blocks */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
            <div className="rounded-xl border border-[#202833] bg-[#0D1117] p-6 shadow-xs">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Cpu className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold mb-2 text-[#F5F7FA] font-sans">Agent Runtime Sandbox</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Secure, isolated execution sandboxes designed to process complex commands, git operations, and code compilation safely.
              </p>
            </div>

            <div className="rounded-xl border border-[#202833] bg-[#0D1117] p-6 shadow-xs">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Layers className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold mb-2 text-[#F5F7FA] font-sans">Multi-Agent Orchestrator</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Coordinates specialized planner, executor, and reviewer agents with structured memory contexts and verification routines.
              </p>
            </div>

            <div className="rounded-xl border border-[#202833] bg-[#0D1117] p-6 shadow-xs">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Shield className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-bold mb-2 text-[#F5F7FA] font-sans">Enterprise Governance</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Enforces strict policy checks, human-in-the-loop approval gates, and multi-tenant security isolation across all workspaces.
              </p>
            </div>
          </div>

          <div className="text-center">
            <Link href="/signup">
              <Button size="lg" className="h-11 px-6 text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9]">
                Deploy ASEP Control Plane
              </Button>
            </Link>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
