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
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />
      
      <main className="flex-1 pt-32 pb-16 relative overflow-hidden">
        {/* Glow Details */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[300px] bg-[#22D3EE]/5 rounded-full blur-[140px] pointer-events-none" />
        
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-12 space-y-4">
            <span className="inline-flex items-center rounded-full border border-[#202833] bg-[#0D1117]/80 px-3 py-1 text-xs font-mono font-medium text-[#22D3EE] shadow-sm">
              PRICING PLANS
            </span>
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl text-[#F5F7FA] font-sans">
              Simple, Transparent Pricing
            </h1>
            <p className="text-base text-[#9CA6B5] font-sans">
              Run secure agent groups locally or in the cloud. Choose the tier matching your team size.
            </p>
          </div>

          {/* Toggle Switch */}
          <div className="flex justify-center mb-16">
            <div className="relative flex items-center p-1 bg-[#111720]/80 border border-[#202833] rounded-full select-none">
              {/* Sliding Pill */}
              <motion.div
                layout
                transition={{ type: "spring", stiffness: 350, damping: 25 }}
                className="absolute h-7 bg-[#22D3EE] rounded-full"
                style={{
                  width: "90px",
                  left: billingPeriod === "monthly" ? "4px" : "98px",
                }}
              />
              <button
                onClick={() => setBillingPeriod("monthly")}
                className={`relative z-10 px-4 py-1 text-[11px] font-mono font-bold w-[90px] transition-colors rounded-full ${
                  billingPeriod === "monthly" ? "text-[#090B0F]" : "text-[#667085] hover:text-[#9CA6B5]"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod("yearly")}
                className={`relative z-10 px-4 py-1 text-[11px] font-mono font-bold w-[90px] transition-colors rounded-full ${
                  billingPeriod === "yearly" ? "text-[#090B0F]" : "text-[#667085] hover:text-[#9CA6B5]"
                }`}
              >
                Yearly
              </button>
            </div>
          </div>

          {/* Pricing Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20 max-w-6xl mx-auto items-stretch">
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
                      className={`w-full font-mono text-xs font-semibold h-11 transition-all rounded-lg ${
                        plan.popular 
                          ? "bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] shadow-[0_0_20px_-5px_rgba(34,211,238,0.4)]" 
                          : "border-[#202833] bg-[#111720] text-[#F5F7FA] hover:bg-[#111720]/80"
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
