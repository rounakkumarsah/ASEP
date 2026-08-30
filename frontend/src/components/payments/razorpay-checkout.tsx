"use client";

/**
 * ASEP — Razorpay Checkout Component
 *
 * Security guarantees:
 *   - RAZORPAY_KEY_SECRET is NEVER present here or in any frontend file.
 *   - The key_id used in Checkout comes from the backend /create-order response.
 *   - Payment verification (HMAC-SHA256) always happens server-side via /verify.
 *
 * Switching Test → Live:
 *   - Change RAZORPAY_KEY_ID in your env (rzp_test_* → rzp_live_*).
 *   - No component changes required.
 */

import * as React from "react";
import { Loader2, CreditCard, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createOrder, verifyPayment } from "@/lib/api/services/payments";

// ---------------------------------------------------------------------------
// Razorpay global type (loaded via CDN script tag)
// ---------------------------------------------------------------------------

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => RazorpayInstance;
  }
}


interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description?: string;
  order_id: string;
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  notes?: Record<string, string>;
  theme?: { color?: string };
  handler: (response: RazorpaySuccessResponse) => void;
  modal?: {
    ondismiss?: () => void;
  };
}

interface RazorpaySuccessResponse {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

interface RazorpayInstance {
  open: () => void;
  close: () => void;
}

// ---------------------------------------------------------------------------
// Component props
// ---------------------------------------------------------------------------

export interface RazorpayCheckoutProps {
  /** Amount in paise. e.g. 49900 = ₹499 */
  amount: number;
  currency?: string;
  /** Display name in the Razorpay modal */
  productName: string;
  description?: string;
  /** Optional user details to prefill the modal */
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  notes?: Record<string, string>;
  /** Called after the backend confirms the payment is captured */
  onSuccess?: (paymentId: string) => void;
  /** Called on user dismissal or network/verification failure */
  onFailure?: (reason: string) => void;
  /** Button label */
  label?: string;
  className?: string;
  disabled?: boolean;
}

// ---------------------------------------------------------------------------
// Load Razorpay checkout.js from CDN (once per session)
// ---------------------------------------------------------------------------

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window !== "undefined" && window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

type CheckoutState = "idle" | "loading" | "success" | "failed";

export function RazorpayCheckout({
  amount,
  currency = "INR",
  productName,
  description,
  prefill,
  notes,
  onSuccess,
  onFailure,
  label = "Pay Now",
  className,
  disabled = false,
}: RazorpayCheckoutProps) {
  const [state, setState] = React.useState<CheckoutState>("idle");
  const [errorMessage, setErrorMessage] = React.useState("");
  const [paidId, setPaidId] = React.useState("");

  const handlePayment = async () => {
    setState("loading");
    setErrorMessage("");

    // 1. Load Razorpay SDK
    const loaded = await loadRazorpayScript();
    if (!loaded) {
      setState("failed");
      setErrorMessage("Failed to load payment gateway. Please check your connection.");
      onFailure?.("script_load_failed");
      return;
    }

    // 2. Create order on the backend
    let orderData: Awaited<ReturnType<typeof createOrder>>;
    try {
      orderData = await createOrder({ amount, currency, description, notes });
    } catch {
      setState("failed");
      setErrorMessage("Could not create payment order. Please try again.");
      onFailure?.("order_creation_failed");
      return;
    }

    // 3. Open Razorpay Checkout modal
    const options: RazorpayOptions = {
      key: orderData.key_id,           // ← public key from backend
      amount: orderData.amount,
      currency: orderData.currency,
      name: productName,
      description,
      order_id: orderData.order_id,
      prefill,
      notes,
      theme: { color: "#22D3EE" },     // ASEP Cyan Accent
      handler: async (response) => {
        // 4. Verify payment signature on the backend
        try {
          const verification = await verifyPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });

          if (verification.success) {
            setState("success");
            setPaidId(verification.payment_id);
            onSuccess?.(verification.payment_id);
          } else {
            throw new Error("Verification returned success=false");
          }
        } catch (err: unknown) {
          setState("failed");
          const apiErr = err as { message?: string };
          setErrorMessage(
            `Verification failed: ${apiErr.message || "Unknown error"}. Please contact support.`
          );
          onFailure?.("verification_failed");
        }
      },
      modal: {
        ondismiss: () => {
          if (state === "loading") {
            setState("idle");
          }
        },
      },
    };

    if (!window.Razorpay) {
      setState("failed");
      setErrorMessage("Razorpay SDK not available.");
      return;
    }
    const rzp = new window.Razorpay(options);
    rzp.open();

  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (state === "success") {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-green-500/20 bg-green-500/5 p-6 text-center">
        <CheckCircle2 className="h-10 w-10 text-green-500" />
        <p className="font-semibold text-green-600 dark:text-green-400">
          Payment Successful!
        </p>
        {paidId && (
          <p className="text-xs text-muted-foreground font-mono">
            Payment ID: {paidId}
          </p>
        )}
      </div>
    );
  }

  if (state === "failed") {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center">
        <XCircle className="h-10 w-10 text-red-500" />
        <p className="font-semibold text-red-600 dark:text-red-400">
          Payment Failed
        </p>
        <p className="text-xs text-muted-foreground">{errorMessage}</p>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setState("idle")}
          className="mt-2"
        >
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <Button
      onClick={handlePayment}
      disabled={disabled || state === "loading"}
      className={className}
      size="lg"
    >
      {state === "loading" ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Processing…
        </>
      ) : (
        <>
          <CreditCard className="mr-2 h-4 w-4" />
          {label}
        </>
      )}
    </Button>
  );
}
