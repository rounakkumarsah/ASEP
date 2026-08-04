"use client";

import * as React from "react";
import { CreditCard, Zap, Building2, History, CheckCircle2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RazorpayCheckout } from "@/components/payments/razorpay-checkout";
import { getPaymentHistory } from "@/lib/api/services/payments";
import type { PaymentRecord } from "@/lib/api/services/payments";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount / 100); // convert paise → INR
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

// ---------------------------------------------------------------------------
// Plans
// ---------------------------------------------------------------------------

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    price: 49900,       // ₹499 in paise
    currency: "INR",
    description: "For individual engineers and small teams",
    icon: Zap,
    features: ["5 concurrent AI agents", "10 GB vector storage", "Email support"],
    badge: null,
  },
  {
    id: "pro",
    name: "Pro",
    price: 199900,      // ₹1,999 in paise
    currency: "INR",
    description: "For growing engineering teams",
    icon: CreditCard,
    features: ["25 concurrent AI agents", "50 GB vector storage", "Priority support", "Custom workflows"],
    badge: "Most Popular",
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: 499900,      // ₹4,999 in paise
    currency: "INR",
    description: "For large organisations with advanced needs",
    icon: Building2,
    features: ["Unlimited AI agents", "500 GB vector storage", "Dedicated support", "SLA guarantee", "SSO & audit logs"],
    badge: null,
  },
] as const;

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function BillingPage() {
  const [payments, setPayments] = React.useState<PaymentRecord[]>([]);
  const [historyLoading, setHistoryLoading] = React.useState(true);
  const [successPlanId, setSuccessPlanId] = React.useState<string | null>(null);

  // Load payment history on mount
  React.useEffect(() => {
    getPaymentHistory(10)
      .then(setPayments)
      .catch(() => setPayments([]))
      .finally(() => setHistoryLoading(false));
  }, []);

  return (
    <div className="space-y-8 p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Billing & Plans</h1>
        <p className="text-muted-foreground mt-1">
          Choose a plan. Payments are secured by Razorpay.
          {" "}
          <span className="text-xs text-yellow-600 dark:text-yellow-400 font-semibold">
            🔐 Test Mode — use card 4111 1111 1111 1111
          </span>
        </p>
      </div>

      {/* Plans */}
      <div className="grid gap-6 md:grid-cols-3">
        {PLANS.map((plan) => {
          const Icon = plan.icon;
          const isSuccess = successPlanId === plan.id;

          return (
            <Card
              key={plan.id}
              className={`relative flex flex-col border ${
                plan.badge
                  ? "border-primary/60 shadow-lg shadow-primary/10"
                  : "border-border/50"
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="px-3 py-0.5 text-xs font-semibold">
                    {plan.badge}
                  </Badge>
                </div>
              )}

              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 mb-1">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                  <CardTitle className="text-lg">{plan.name}</CardTitle>
                </div>
                <CardDescription className="text-xs">{plan.description}</CardDescription>
                <p className="text-3xl font-extrabold mt-2">
                  {formatCurrency(plan.price, plan.currency)}
                  <span className="text-sm font-normal text-muted-foreground">/mo</span>
                </p>
              </CardHeader>

              <CardContent className="flex flex-col flex-1 gap-4">
                <ul className="space-y-1.5 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>

                {isSuccess ? (
                  <div className="flex items-center justify-center gap-2 rounded-lg bg-green-500/10 p-3 text-green-600 dark:text-green-400 text-sm font-semibold">
                    <CheckCircle2 className="h-4 w-4" />
                    Activated!
                  </div>
                ) : (
                  <RazorpayCheckout
                    amount={plan.price}
                    currency={plan.currency}
                    productName={`ASEP ${plan.name}`}
                    description={plan.description}
                    notes={{ plan: plan.id }}
                    label={`Subscribe to ${plan.name}`}
                    className="w-full"
                    onSuccess={() => {
                      setSuccessPlanId(plan.id);
                      // Refresh payment history
                      getPaymentHistory(10).then(setPayments).catch(() => {});
                    }}
                    onFailure={(reason) => {
                      console.warn("Payment failed:", reason);
                    }}
                  />
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Payment History */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Payment History</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <p className="text-sm text-muted-foreground py-4 text-center">Loading…</p>
          ) : payments.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No payments yet.
            </p>
          ) : (
            <div className="divide-y divide-border/50">
              {payments.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-3 text-sm"
                >
                  <div className="space-y-0.5">
                    <p className="font-medium font-mono text-xs text-muted-foreground">
                      {p.razorpay_payment_id ?? p.razorpay_order_id}
                    </p>
                    {p.description && (
                      <p className="text-xs text-muted-foreground">{p.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold">
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
