import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { ShieldAlert, Rocket } from "lucide-react";

export const metadata: Metadata = {
  title: "About | ASEP",
  description: "Learn about the mission, engineering philosophy, and vision behind the Autonomous Software Engineering Platform.",
  openGraph: {
    title: "About Us - ASEP",
    description: "Learn about the mission, engineering philosophy, and vision behind the Autonomous Software Engineering Platform.",
    type: "website",
  },
};

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-[#F5F7FA] font-sans">
              About ASEP
            </h1>
            <p className="text-base text-[#9CA6B5] font-sans">
              Empowering enterprise teams to orchestrate autonomous AI agent workflows with zero compromise on reliability, safety, and governance.
            </p>
          </div>

          {/* Mission and Vision Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20 max-w-5xl mx-auto">
            <div className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <Rocket className="h-5 w-5" />
              </div>
              <h2 className="text-xl font-bold tracking-tight mb-2 text-[#F5F7FA]">Engineering Vision</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                We believe that the future of software development lies in collaborative loops between human engineers and autonomous AI agents. ASEP provides the production-grade control plane that allows agents to plan, compile code, execute tests, and manage repositories safely under strict governance.
              </p>
            </div>

            <div className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl">
              <div className="h-10 w-10 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <h2 className="text-xl font-bold tracking-tight mb-2 text-[#F5F7FA]">Safety & Reliability</h2>
              <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                Autonomous code generation requires execution capabilities to solve complex tasks. ASEP enforces strict human-in-the-loop approval gates, containerized execution sandboxes, and immutable audit logs to protect enterprise infrastructure.
              </p>
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
