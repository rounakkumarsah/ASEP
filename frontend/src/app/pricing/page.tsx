"use client";

import React, { useState } from "react";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { User, Users, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PricingCard } from "@/components/ui/pricing-card";
import Link from "next/link";
import { motion } from "framer-motion";

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly");

  const plans = [
    {
      name: "Developer",
      price: "$0",
      period: "",
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
      price: billingPeriod === "monthly" ? "$49" : "$39",
      period: billingPeriod === "monthly" ? "/user/month" : "/user/month, billed annually",
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
      period: "",
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
    <div className="flex min-h-screen flex-col bg-background dark:bg-[#090B0F] text-foreground transition-colors duration-300">
      <LandingNavbar />
      
      <main className="flex-1 pt-28 sm:pt-32 pb-16 relative overflow-hidden">
        {/* Glow Details */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[300px] bg-[#22D3EE]/5 rounded-full blur-[140px] pointer-events-none" />
        
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-12 space-y-3 sm:space-y-4">
            <span className="inline-flex items-center rounded-full border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117]/80 px-3 py-1 text-xs font-mono font-medium text-primary shadow-sm">
              PRICING PLANS
            </span>
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground font-sans">
              Simple, Transparent Pricing
            </h1>
            <p className="text-base sm:text-lg text-muted-foreground font-sans leading-relaxed">
              Run secure agent groups locally or in the cloud. Choose the tier matching your team size.
            </p>
          </div>

          {/* Toggle Switch */}
          <div className="flex justify-center mb-12 sm:mb-16">
            <div className="relative flex items-center p-1 bg-muted/60 dark:bg-[#111720]/80 border border-border/80 dark:border-[#202833] rounded-full select-none shadow-sm">
              {/* Sliding Pill */}
              <motion.div
                layout
                transition={{ type: "spring", stiffness: 350, damping: 25 }}
                className="absolute h-7 bg-[#22D3EE] rounded-full shadow-sm"
                style={{
                  width: "90px",
                  left: billingPeriod === "monthly" ? "4px" : "98px",
                }}
              />
              <button
                onClick={() => setBillingPeriod("monthly")}
                className={`relative z-10 px-4 py-1 text-[11px] font-mono font-bold w-[90px] transition-colors rounded-full ${
                  billingPeriod === "monthly" ? "text-[#090B0F]" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod("yearly")}
                className={`relative z-10 px-4 py-1 text-[11px] font-mono font-bold w-[90px] transition-colors rounded-full ${
                  billingPeriod === "yearly" ? "text-[#090B0F]" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Yearly
              </button>
            </div>
          </div>

          {/* Pricing Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 mb-16 sm:mb-20 max-w-6xl mx-auto items-stretch">
            {plans.map((plan) => (
              <PricingCard
                key={plan.name}
                name={plan.name}
                price={plan.price}
                period={plan.period}
                description={plan.description}
                icon={plan.name === "Developer" ? User : plan.name === "Team" ? Users : Building2}
                features={plan.features}
                isPopular={plan.popular}
                action={
                  <Link href={plan.name === "Enterprise" ? "/contact" : "/signup"} className="w-full">
                    <Button 
                      className={`w-full font-mono text-xs font-semibold h-11 transition-all rounded-xl min-h-[44px] ${
                        plan.popular 
                          ? "bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] shadow-[0_0_20px_-5px_rgba(34,211,238,0.4)]" 
                          : "border-border bg-card hover:bg-accent text-foreground"
                      }`}
                      variant={plan.popular ? "default" : "outline"}
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                }
              />
            ))}
          </div>
          
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
