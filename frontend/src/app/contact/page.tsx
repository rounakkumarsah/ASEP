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
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
              Contact Our Team
            </h1>
            <p className="mt-4 text-xl text-muted-foreground">
              Have security, architecture, or license questions? We&apos;re here to help.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-5xl mx-auto mb-20">
            {/* Contact details */}
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold tracking-tight mb-4">Get in Touch</h2>
                <p className="text-muted-foreground leading-relaxed">
                  For bug reports, security disclosures, or enterprise license queries, drop us a line and an engineer will reply shortly.
                </p>
              </div>

              <div className="space-y-6">
                <div className="flex items-center space-x-4">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    <Mail className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold">Email</h3>
                    <p className="text-sm text-muted-foreground">support@asep.internal</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    <MessageSquare className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold">Community Support</h3>
                    <p className="text-sm text-muted-foreground">github.com/rounakkumarsah/ASEP/issues</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Simple Contact Form */}
            <div className="rounded-2xl border border-border/50 bg-card p-8 shadow-sm">
              <ContactForm />
            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
