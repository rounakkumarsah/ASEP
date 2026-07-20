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
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
              About ASEP
            </h1>
            <p className="mt-4 text-xl text-muted-foreground">
              Empowering developers and enterprise teams to run agent workflows locally, with zero compromise on safety and data governance.
            </p>
          </div>

          {/* Mission and Vision Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-20 max-w-5xl mx-auto">
            <div>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <Rocket className="h-6 w-6" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight mb-4">Our Vision</h2>
              <p className="text-muted-foreground leading-relaxed">
                We believe that the future of software engineering lies in collaborative loops between human engineers and autonomous AI agents. Our goal is to build the standard, open framework that allows agents to compile code, debug builds, run tests, and manage repositories safely without leaving the local environment.
              </p>
            </div>

            <div>
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight mb-4">Safety First</h2>
              <p className="text-muted-foreground leading-relaxed">
                AI agents require code compilation and shell execution capabilities to solve real-world problems. Giving models unlimited access to host environments is highly risky. ASEP solves this by sandboxing operations in Docker, and monitoring every output with human approval gates.
              </p>
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
