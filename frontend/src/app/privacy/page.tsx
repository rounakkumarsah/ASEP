import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";

export const metadata: Metadata = {
  title: "Privacy Policy | ASEP",
  description: "Privacy policies governing workspace environments and locally hosted logs in ASEP.",
};

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-24 pb-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-extrabold tracking-tight mb-2 text-[#F5F7FA] font-mono">Privacy Policy</h1>
          <p className="text-[11px] font-mono text-[#667085] mb-8">Last Updated: August 6, 2026</p>
          
          <div className="space-y-6 text-xs text-[#9CA6B5] leading-relaxed font-sans">
            <section className="p-5 border border-[#202833] bg-[#0D1117] rounded-xl space-y-2">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">1. Local Execution & Data Privacy</h2>
              <p>
                ASEP prioritizes local containment. Your codebase assets, agent shell execution logs, and memory indexes are stored on your local workspace host. No telemetry containing raw source code is sent to external servers.
              </p>
            </section>

            <section className="p-5 border border-[#202833] bg-[#0D1117] rounded-xl space-y-2">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">2. API Integrations</h2>
              <p>
                If you configure remote LLM execution providers, their respective privacy policies apply to any prompts dispatched during agent cycles.
              </p>
            </section>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
