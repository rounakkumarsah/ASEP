"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";

interface UpgradeModalProps {
  isOpen?: boolean;
  onClose?: () => void;
}



export function UpgradeModal({ isOpen: externalOpen, onClose: externalClose }: UpgradeModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (externalOpen !== undefined) {
      setIsOpen(externalOpen);
    }
  }, [externalOpen]);

  useEffect(() => {
    const handleRateLimit = () => {
      setIsOpen(true);
    };

    window.addEventListener("auth:rate_limit", handleRateLimit);
    return () => window.removeEventListener("auth:rate_limit", handleRateLimit);
  }, []);

  const handleClose = () => {
    setIsOpen(false);
    if (externalClose) externalClose();
  };

  const handleUpgrade = async (tier: "pro" | "enterprise") => {
    setLoading(true);
    if (typeof window !== "undefined" && (window as unknown as { posthog?: { capture: (evt: string, props?: Record<string, unknown>) => void } }).posthog) {
      (window as unknown as { posthog: { capture: (evt: string, props?: Record<string, unknown>) => void } }).posthog.capture("upgrade_clicked", { tier });
    }
    try {
      const response = await apiClient.post("/payments/create-order", { plan: tier });

      const { razorpay_order_id, key_id, amount } = response.data as {
        razorpay_order_id: string;
        key_id?: string;
        amount?: number;
      };

      // Initialize Razorpay checkout if loaded
      const win = typeof window !== "undefined" ? (window as unknown as { Razorpay?: new (opts: unknown) => { open: () => void } }) : {};
      if (win.Razorpay) {
        const options = {
          key: key_id || "rzp_test_mock_key",
          amount: amount || 299900,
          currency: "INR",
          name: "ASEP Copilot Pro",
          description: "Unlimited Deep Research & Multimodal Copilot",
          order_id: razorpay_order_id,
          handler: function (res: { razorpay_payment_id: string }) {
            alert(`Payment successful! Payment ID: ${res.razorpay_payment_id}`);
            handleClose();
          },
          theme: { color: "#3B82F6" },
        };
        const rzp = new win.Razorpay(options);
        rzp.open();
      } else {
        alert(`Razorpay Checkout initialized for order: ${razorpay_order_id}.`);
        handleClose();
      }
    } catch (err: unknown) {
      const apiErr = err as { message?: string };
      alert(apiErr.message || "Failed to initialize payment checkout.");
    } finally {
      setLoading(false);
    }
  };



  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-zinc-900 border border-zinc-800 p-6 text-white shadow-2xl">
        <div className="flex justify-between items-start mb-4">
          <div>
            <span className="inline-block px-3 py-1 text-xs font-semibold text-amber-400 bg-amber-950/40 border border-amber-800 rounded-full mb-2">
              Free Quota Limit Exceeded
            </span>
            <h2 className="text-2xl font-bold text-zinc-100">Upgrade to Copilot Pro</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-zinc-400 hover:text-white text-xl font-semibold p-1"
          >
            ✕
          </button>
        </div>

        <p className="text-zinc-400 text-sm mb-6">
          You have reached your free limit of 10 queries/day. Upgrade to Pro for unlimited Deep Research, Multimodal Vision error troubleshooting, and GraphRAG knowledge searches.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 hover:border-blue-500/50 transition">
            <h3 className="font-semibold text-zinc-200">Pro Plan</h3>
            <p className="text-2xl font-extrabold text-blue-400 my-1">₹2,999<span className="text-xs text-zinc-400 font-normal">/mo</span></p>
            <ul className="text-xs text-zinc-400 space-y-1 mb-4">
              <li>✓ Unlimited Deep Research</li>
              <li>✓ Multimodal Screenshot Copilot</li>
              <li>✓ Local GraphRAG Engine</li>
            </ul>
            <button
              onClick={() => handleUpgrade("pro")}
              disabled={loading}
              className="w-full py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 font-semibold text-xs transition"
            >
              {loading ? "Processing..." : "Upgrade Pro"}
            </button>
          </div>

          <div className="p-4 rounded-xl bg-zinc-950 border border-amber-500/30 hover:border-amber-500 transition">
            <h3 className="font-semibold text-amber-300">Enterprise</h3>
            <p className="text-2xl font-extrabold text-amber-400 my-1">₹9,999<span className="text-xs text-zinc-400 font-normal">/mo</span></p>
            <ul className="text-xs text-zinc-400 space-y-1 mb-4">
              <li>✓ Everything in Pro</li>
              <li>✓ Custom Graph DB & Vectors</li>
              <li>✓ Priority 24/7 SLA</li>
            </ul>
            <button
              onClick={() => handleUpgrade("enterprise")}
              disabled={loading}
              className="w-full py-2 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 font-semibold text-xs text-black transition"
            >
              {loading ? "Processing..." : "Contact Sales"}
            </button>
          </div>
        </div>

        <div className="text-center text-xs text-zinc-500">
          Secured by Razorpay. Cancel anytime.
        </div>
      </div>
    </div>
  );
}
