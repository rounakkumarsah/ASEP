import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";

export const metadata: Metadata = {
  title: "Terms of Service | ASEP",
  description: "Terms and conditions for using the Autonomous Software Engineering Platform.",
};

export default function TermsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-extrabold tracking-tight mb-6">Terms of Service</h1>
          <p className="text-muted-foreground mb-8">Last Updated: July 20, 2026</p>
          
          <div className="space-y-6 text-muted-foreground leading-relaxed">
            <section>
              <h2 className="text-xl font-bold text-foreground mb-3">1. Acceptance of Terms</h2>
              <p>
                By accessing or using the ASEP platform, you agree to comply with and be bound by these Terms of Service. If you do not agree, please do not use our services.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-foreground mb-3">2. Description of Service</h2>
              <p>
                ASEP provides a local control plane and isolated sandbox execution environments for running and orchestrating autonomous software developer agents.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-foreground mb-3">3. User Responsibilities</h2>
              <p>
                You are responsible for obtaining appropriate license credentials for any third-party language models integrated with your agent workflows, and for maintaining security of your local configurations.
              </p>
            </section>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
