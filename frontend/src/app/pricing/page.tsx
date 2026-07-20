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
      description: "Perfect for individual developers running locally.",
      features: [
        "Single local agent workspace sandbox",
        "Git & terminal tool integration",
        "Local memory and filesystem RAG",
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
        "Audit logs and custom alerts",
        "HITL gate slack/email webhooks",
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
        "Bespoke security governance logic",
        "24/7 Dedicated account engineering",
        "SLA guarantees",
      ],
      cta: "Contact Sales",
      popular: false,
    },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
              Simple, Transparent Pricing
            </h1>
            <p className="mt-4 text-xl text-muted-foreground">
              Run secure agent groups locally. Choose the plan that matches your security and team size requirements.
            </p>
          </div>

          {/* Pricing cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20 max-w-6xl mx-auto">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border bg-card p-8 shadow-sm flex flex-col justify-between ${
                  plan.popular ? "border-primary ring-1 ring-primary" : "border-border/50"
                }`}
              >
                {plan.popular && (
                  <span className="absolute top-0 right-6 transform -translate-y-1/2 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
                    Most Popular
                  </span>
                )}
                <div>
                  <h3 className="text-2xl font-bold tracking-tight mb-2">{plan.name}</h3>
                  <p className="text-sm text-muted-foreground mb-6 min-h-[40px]">{plan.description}</p>
                  <div className="flex items-baseline mb-6">
                    <span className="text-4xl font-extrabold tracking-tight">{plan.price}</span>
                    {plan.period && <span className="text-sm text-muted-foreground ml-1">{plan.period}</span>}
                  </div>
                  <ul className="space-y-4 mb-8">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start text-sm">
                        <Check className="h-4 w-4 text-primary shrink-0 mr-3 mt-0.5" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <Link href="/login" className="w-full">
                  <Button className="w-full font-semibold" variant={plan.popular ? "default" : "outline"}>
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
