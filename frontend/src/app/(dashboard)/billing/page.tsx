"use client";

import * as React from "react";
import Link from "next/link";
import { CreditCard, Zap, Building2, History, CheckCircle2, ShieldCheck, FileText, ArrowRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RazorpayCheckout } from "@/components/payments/razorpay-checkout";
import { getPaymentHistory } from "@/lib/api/services/payments";
import type { PaymentRecord } from "@/lib/api/services/payments";
import { EmptyState } from "@/components/ui/empty-state";
import { PricingCard } from "@/components/ui/pricing-card";

function formatCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount / 100);
}

function statusBadgeVariant(
  status: PaymentRecord["status"]
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "captured":
      return "default";
    case "created":
    case "authorized":
      return "secondary";
    case "failed":
      return "destructive";
    default:
      return "outline";
  }
}

export default function BillingPage() {
  const [payments, setPayments] = React.useState<PaymentRecord[]>([]);
  const [historyLoading, setHistoryLoading] = React.useState(true);
  const [successPlanId, setSuccessPlanId] = React.useState<string | null>(null);
  const [billingInterval, setBillingInterval] = React.useState<"monthly" | "annual">("monthly");

  const isTestMode =
    process.env.NEXT_PUBLIC_PAYMENT_MODE === "test" ||
    (typeof window !== "undefined" && window.location.hostname === "localhost");

  React.useEffect(() => {
    getPaymentHistory(10)
      .then(setPayments)
      .catch(() => setPayments([]))
      .finally(() => setHistoryLoading(false));
  }, []);

  const plans = [
    {
      id: "free",
      name: "Free Community",
      price: 0,
      displayPrice: "₹0",
      period: "/month",
      currency: "INR",
      description: "For individual developers exploring autonomous agents.",
      icon: Zap,
      features: [
        "10 Daily AI inference requests",
        "1 Active session workspace",
        "Community Discord support",
        "Standard latency queue",
      ],
      isPopular: false,
      isFree: true,
    },
    {
      id: "pro",
      name: "Professional",
      price: billingInterval === "monthly" ? 199900 : 1919000,
      displayPrice: billingInterval === "monthly" ? "₹1,999" : "₹19,190",
      period: billingInterval === "monthly" ? "/month" : "/year",
      currency: "INR",
      description: "For engineering teams building autonomous production workflows.",
      icon: CreditCard,
      features: [
        "Unlimited Daily AI inferences",
        "25 Concurrent Agent runs",
        "Human-in-the-Loop governance policies",
        "Priority LLM routing (<15ms)",
        "Automated GST invoice generation",
        "Email & Slack priority support",
      ],
      isPopular: true,
      isFree: false,
    },
    {
      id: "enterprise",
      name: "Enterprise Custom",
      price: 499900,
      displayPrice: "Custom",
      period: "billed annually",
      currency: "INR",
      description: "For scaling organizations with custom governance & compliance.",
      icon: Building2,
      features: [
        "Custom isolated execution VPCs",
        "Air-gapped on-premise LLM support",
        "Custom SLA guarantees (99.99%)",
        "Dedicated Solutions Architect",
        "SOC2 & HIPAA Compliance reports",
        "Custom billing & invoicing terms",
      ],
      isPopular: false,
      isEnterprise: true,
    },
  ];

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto font-sans">
      {/* Header with Security & Test Mode Indicator */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground font-mono">
            Billing & Subscription
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your organization tier, payment methods, and automated GST receipts.
          </p>
        </div>
        <div>
          {isTestMode ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
              🔐 Test Mode (Sandbox Enabled)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="w-3.5 h-3.5" /> Secure payments powered by Razorpay
            </span>
          )}
        </div>
      </div>

      {/* Interval Selector */}
      <div className="flex items-center justify-center">
        <div className="inline-flex p-1 bg-[#111720] border border-[#202833] rounded-xl text-xs font-mono">
          <button
            type="button"
            onClick={() => setBillingInterval("monthly")}
            className={`px-4 py-1.5 rounded-lg transition-all ${
              billingInterval === "monthly"
                ? "bg-[#22D3EE] text-[#090B0F] font-bold shadow-sm"
                : "text-[#9CA6B5] hover:text-[#F5F7FA]"
            }`}
          >
            Monthly Billing
          </button>
          <button
            type="button"
            onClick={() => setBillingInterval("annual")}
            className={`px-4 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              billingInterval === "annual"
                ? "bg-[#22D3EE] text-[#090B0F] font-bold shadow-sm"
                : "text-[#9CA6B5] hover:text-[#F5F7FA]"
            }`}
          >
            Annual Billing
            <span className="text-[10px] bg-[#2DD4A3]/20 text-[#2DD4A3] border border-[#2DD4A3]/30 px-1.5 py-0.2 rounded-full font-bold">
              Save 20%
            </span>
          </button>
        </div>
      </div>

      {/* Plans Comparison Grid */}
      <div className="grid gap-6 md:grid-cols-3">
        {plans.map((plan) => {
          const Icon = plan.icon;
          const isSuccess = successPlanId === plan.id;

          return (
            <PricingCard
              key={plan.id}
              name={plan.name}
              price={plan.displayPrice}
              period={plan.period}
              description={plan.description}
              icon={Icon}
              features={plan.features}
              isPopular={plan.isPopular}
              action={
                isSuccess ? (
                  <div className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500/10 py-3 text-emerald-400 text-sm font-semibold border border-emerald-500/20">
                    <CheckCircle2 className="h-4 w-4" />
                    Subscription Activated!
                  </div>
                ) : plan.isFree ? (
                  <Button variant="outline" disabled className="w-full text-xs font-mono">
                    Current Active Plan
                  </Button>
                ) : plan.isEnterprise ? (
                  <Link href="/contact" className="w-full">
                    <Button variant="outline" className="w-full text-xs font-mono border-[#202833] hover:border-[#22D3EE] hover:text-[#22D3EE]">
                      Contact Enterprise Sales <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                ) : (
                  <RazorpayCheckout
                    amount={plan.price}
                    currency={plan.currency}
                    productName={`ASEP ${plan.name} (${billingInterval})`}
                    description={plan.description}
                    notes={{ plan: plan.id, interval: billingInterval }}
                    label={`Upgrade to ${plan.name}`}
                    className="w-full"
                    onSuccess={() => {
                      setSuccessPlanId(plan.id);
                      getPaymentHistory(10).then(setPayments).catch(() => {});
                    }}
                    onFailure={(reason) => {
                      console.warn("Payment failed:", reason);
                    }}
                  />
                )
              }
            />
          );
        })}
      </div>

      {/* Trust Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
        <div className="p-4 rounded-xl border border-border/40 bg-card/30 flex items-center gap-3 text-xs text-muted-foreground">
          <ShieldCheck className="w-5 h-5 text-primary shrink-0" />
          <span>256-Bit SSL End-to-End Encrypted Checkout</span>
        </div>
        <div className="p-4 rounded-xl border border-border/40 bg-card/30 flex items-center gap-3 text-xs text-muted-foreground">
          <FileText className="w-5 h-5 text-primary shrink-0" />
          <span>Automated GST Tax Invoicing & Receipts</span>
        </div>
        <div className="p-4 rounded-xl border border-border/40 bg-card/30 flex items-center gap-3 text-xs text-muted-foreground">
          <Zap className="w-5 h-5 text-primary shrink-0" />
          <span>Instant Provisioning with Zero Downtime</span>
        </div>
      </div>

      {/* Payment History & Invoices */}
      <Card className="border-border/40 bg-card/30">
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-primary" />
            <div>
              <CardTitle className="text-base font-mono font-bold">Billing & Invoices History</CardTitle>
              <CardDescription className="text-xs">Past transactions and downloadable GST compliant invoices.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <p className="text-sm text-muted-foreground py-6 text-center font-mono">Loading transaction records…</p>
          ) : payments.length === 0 ? (
            <EmptyState
              icon={History}
              title="No invoices found"
              description="Your payment history will appear here once you subscribe to a paid tier."
            />
          ) : (
            <div className="divide-y divide-border/40">
              {payments.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-3 text-sm"
                >
                  <div className="space-y-0.5">
                    <p className="font-medium font-mono text-xs text-foreground">
                      {p.razorpay_payment_id ?? p.razorpay_order_id}
                    </p>
                    {p.description && (
                      <p className="text-xs text-muted-foreground">{p.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold font-mono text-foreground">
                      {formatCurrency(p.amount, p.currency)}
                    </span>
                    <Badge variant={statusBadgeVariant(p.status)} className="capitalize text-xs">
                      {p.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
