import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy | ASEP",
  description: "Privacy policies governing data protection, telemetry isolation, and processing in ASEP.",
};

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-28 pb-20">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="mb-10">
            <h1 className="text-3xl font-extrabold tracking-tight mb-2 text-[#F5F7FA] font-mono">
              Privacy Policy
            </h1>
            <p className="text-xs font-mono text-[#667085]">
              Effective Date: August 22, 2026 | Version 1.0.0
            </p>
          </div>
          
          <div className="space-y-6 text-xs text-[#9CA6B5] leading-relaxed">
            <section className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl space-y-3">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">1. Overview & Privacy Commitment</h2>
              <p>
                ASEP (&ldquo;we&rdquo;, &ldquo;our&rdquo;, &ldquo;us&rdquo;) provides sovereign, autonomous software engineering platform tools. We are committed to protecting the privacy, confidentiality, and integrity of your source code and personal data. This Privacy Policy details how we collect, store, process, and safeguard information across our website, API, and platform services.
              </p>
            </section>

            <section className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl space-y-3">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">2. Sovereign Code Isolation & Telemetry</h2>
              <p>
                <strong>Zero Training on Customer Code:</strong> We do not use your source code, repository structures, or proprietary prompts to train foundation models without your explicit opt-in consent.
              </p>
              <p>
                <strong>Local & Isolated Sandboxes:</strong> Agent code executions run in isolated containers or your self-hosted runner infrastructure. Ephemeral shell sessions and container logs are deleted upon session termination according to your retention policies.
              </p>
            </section>

            <section className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl space-y-3">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">3. Information We Collect</h2>
              <ul className="list-disc pl-5 space-y-1.5">
                <li><strong>Account Credentials:</strong> Name, email address, password hashes (Argon2id/Bcrypt), MFA TOTP metadata, and workspace company name.</li>
                <li><strong>Billing Information:</strong> Billing address, subscription tier, transaction receipts, and payment method identifiers managed securely through PCI-DSS compliant processors.</li>
                <li><strong>Operational Telemetry:</strong> Anonymized platform performance metrics, error traces (via Sentry), request latencies, and API usage quotas.</li>
                <li><strong>Audit & Security Logs:</strong> IP addresses, user agent strings, login events, and security access logs stored for fraud prevention and audit compliance.</li>
              </ul>
            </section>

            <section className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl space-y-3">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">4. Third-Party Sub-Processors</h2>
              <p>We partner with industry-leading infrastructure providers under strict Data Processing Agreements:</p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li><strong>Cloud Database:</strong> Neon PostgreSQL (Encrypted at rest with AES-256).</li>
                <li><strong>In-Memory Cache & Queues:</strong> Upstash Redis / Redis Enterprise.</li>
                <li><strong>Vector & Graph Indices:</strong> Qdrant Cloud & Neo4j Aura.</li>
                <li><strong>Transactional Email:</strong> Resend (DKIM/SPF authenticated).</li>
                <li><strong>Bot Protection:</strong> Cloudflare Turnstile (Privacy-preserving verification).</li>
                <li><strong>Payment Gateway:</strong> Razorpay (PCI-DSS Level 1 certified).</li>
              </ul>
            </section>

            <section className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl space-y-3">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">5. Your Data Rights (GDPR & CCPA/CPRA)</h2>
              <p>Depending on your location, you hold statutory rights regarding your personal data:</p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li><strong>Access & Portability:</strong> Request an export of your account data and project configurations.</li>
                <li><strong>Rectification:</strong> Update or correct your profile details via the Settings portal.</li>
                <li><strong>Erasure (&ldquo;Right to be Forgotten&rdquo;):</strong> Request full deletion of your account, workspace data, and audit history.</li>
                <li><strong>Opt-Out:</strong> Manage telemetry and analytics tracking preferences in your workspace preferences.</li>
              </ul>
            </section>

            <section className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl space-y-3">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">6. Cookies & Security Tokens</h2>
              <p>
                We use secure, HttpOnly, SameSite=Strict cookies solely for session maintenance and CSRF protection. We do not use cross-site tracking cookies or sell your personal information.
              </p>
            </section>

            <section className="p-6 border border-[#202833] bg-[#0D1117] rounded-xl space-y-3">
              <h2 className="text-sm font-mono font-bold text-[#F5F7FA]">7. Contact Our Data Protection Officer</h2>
              <p>
                To exercise any privacy rights or request a Data Processing Agreement (DPA), contact our DPO at{" "}
                <a href="mailto:privacy@asep.dev" className="text-[#22D3EE] hover:underline font-mono">
                  privacy@asep.dev
                </a>{" "}
                or review our <Link href="/terms" className="text-[#22D3EE] hover:underline font-semibold">Terms of Service</Link>.
              </p>
            </section>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}

