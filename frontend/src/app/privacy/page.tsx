import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";

export const metadata: Metadata = {
  title: "Privacy Policy | ASEP",
  description: "Privacy policies governing workspace environments and locally hosted logs in ASEP.",
};

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-extrabold tracking-tight mb-6">Privacy Policy</h1>
          <p className="text-muted-foreground mb-8">Last Updated: July 20, 2026</p>
          
          <div className="space-y-6 text-muted-foreground leading-relaxed">
            <section>
              <h2 className="text-xl font-bold text-foreground mb-3">1. Local Execution & Data Privacy</h2>
              <p>
                ASEP prioritizes local containment. Your codebase assets, agent shell execution logs, and memory indexes are stored on your local workspace host. No telemetry containing raw source code is sent to external servers.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-foreground mb-3">2. API Integrations</h2>
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
