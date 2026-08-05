import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { Mail, MessageSquare } from "lucide-react";
import { ContactForm } from "@/components/landing/contact-form";

export const metadata: Metadata = {
  title: "Contact | ASEP",
  description: "Get in touch with the ASEP engineering team for security inquiries, feedback, and sales support.",
  openGraph: {
    title: "Contact Us - ASEP",
    description: "Get in touch with the ASEP engineering team for security inquiries, feedback, and sales support.",
    type: "website",
  },
};

export default function ContactPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-[#F5F7FA] font-sans">
              Contact Engineering
            </h1>
            <p className="text-base text-[#9CA6B5] font-sans">
              Have security, architecture, or enterprise license questions? Contact our core team.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-5xl mx-auto mb-20">
            {/* Contact details */}
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold tracking-tight mb-2 text-[#F5F7FA] font-sans">Get in Touch</h2>
                <p className="text-xs text-[#9CA6B5] leading-relaxed font-sans">
                  For bug disclosures, infrastructure security reports, or enterprise SLA queries, our engineering team responds promptly.
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-3 p-4 border border-[#202833] bg-[#0D1117] rounded-xl">
                  <div className="h-9 w-9 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE]">
                    <Mail className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold font-mono text-[#F5F7FA]">Email Engineering</h3>
                    <p className="text-xs font-mono text-[#9CA6B5]">support@asep-ai.vercel.app</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 p-4 border border-[#202833] bg-[#0D1117] rounded-xl">
                  <div className="h-9 w-9 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE]">
                    <MessageSquare className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold font-mono text-[#F5F7FA]">Developer Community</h3>
                    <p className="text-xs font-mono text-[#9CA6B5]">github.com/rounakkumarsah/ASEP</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Contact Form */}
            <div className="border border-[#202833] bg-[#0D1117] p-6 rounded-xl shadow-xs">
              <ContactForm />
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
