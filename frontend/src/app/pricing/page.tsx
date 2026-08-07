import type { Metadata } from "next";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Pricing | ASEP",
  description: "Flexible deployment pricing tiers for local developer groups and enterprise teams.",
  openGraph: {
    title: "Pricing Plans - ASEP",
    description: "Flexible deployment pricing tiers for local developer groups and enterprise teams.",
    type: "website",
  },
};

export default function PricingPage() {
  const plans = [
    {
      name: "Developer",
      price: "$0",
      description: "Ideal for individual engineers exploring autonomous agent orchestration.",
      features: [
        "Single workspace sandbox",
        "Git & terminal tool integration",
        "Memory & knowledge RAG",
        "Up to 2 active sessions",
        "Community support",
      ],
      cta: "Start Free",
      popular: false,
    },
    {
      name: "Team",
      price: "$49",
      period: "/user/month",
      description: "Collaborative control plane for engineering teams.",
      features: [
        "Unlimited sandbox workspaces",
        "Decoupled multi-agent orchestration",
        "Shared Neo4j knowledge graphs",
        "Audit logs & custom alerts",
        "HITL gate webhook notifications",
        "Priority support",
      ],
      cta: "Start Team Trial",
      popular: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      description: "Bespoke compliance policies and custom LLM runtimes.",
      features: [
        "Air-gapped private deployments",
        "Single Sign-On (SAML/OIDC)",
        "Zero data retention LLM integrations",
        "Bespoke governance logic",
        "24/7 Dedicated account engineering",
        "SLA guarantees",
      ],
      cta: "Contact Sales",
      popular: false,
    },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-[#F5F7FA] font-sans">
              Simple, Transparent Pricing
            </h1>
            <p className="text-base text-[#9CA6B5] font-sans">
              Run secure agent groups locally or in the cloud. Choose the tier matching your team size.
            </p>
          </div>

          {/* Pricing cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20 max-w-6xl mx-auto">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-xl border bg-[#0D1117] p-6 shadow-xs flex flex-col justify-between ${
                  plan.popular ? "border-[#22D3EE]" : "border-[#202833]"
                }`}
              >
                {plan.popular && (
                  <span className="absolute top-0 right-6 transform -translate-y-1/2 rounded bg-[#22D3EE] px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase text-[#090B0F]">
                    Most Popular
                  </span>
                )}
                <div>
                  <h3 className="text-xl font-bold tracking-tight mb-2 text-[#F5F7FA] font-sans">{plan.name}</h3>
                  <p className="text-xs text-[#9CA6B5] mb-6 min-h-[36px] font-sans">{plan.description}</p>
                  <div className="flex items-baseline mb-6 font-mono">
                    <span className="text-3xl font-extrabold tracking-tight text-[#F5F7FA]">{plan.price}</span>
                    {plan.period && <span className="text-xs text-[#667085] ml-1">{plan.period}</span>}
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start text-xs font-sans text-[#F5F7FA]">
                        <Check className="h-3.5 w-3.5 text-[#22D3EE] shrink-0 mr-2.5 mt-0.5" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <Link href={plan.name === "Enterprise" ? "/contact" : "/signup"} className="w-full">
                  <Button 
                    className={`w-full font-mono text-xs font-semibold h-10 ${
                      plan.popular 
                        ? "bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9]" 
                        : "border-[#202833] bg-[#111720] text-[#F5F7FA] hover:bg-[#111720]/80"
                    }`}
                    variant={plan.popular ? "default" : "outline"}
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
