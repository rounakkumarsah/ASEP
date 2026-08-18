"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/providers/auth-provider";
import { AlertCircle, ArrowRight } from "lucide-react";

export function EmailVerificationBanner() {
  const { user } = useAuth();

  if (!user || user.email_verified) {
    return null;
  }

  return (
    <div className="bg-[#F5B942]/10 border-b border-[#F5B942]/20 px-4 py-2 text-xs font-mono text-[#F5B942] flex items-center justify-between shadow-xs">
      <div className="flex items-center gap-2">
        <AlertCircle className="w-4 h-4 text-[#F5B942] shrink-0" />
        <span>
          Your email address is unverified. Please verify your email to unlock all platform features.
        </span>
      </div>
      <Link
        href={`/verify-email?email=${encodeURIComponent(user.email || "")}`}
        className="underline hover:text-white font-semibold flex items-center gap-1 shrink-0 ml-4"
      >
        Verify Email <ArrowRight className="w-3 h-3" />
      </Link>
    </div>
  );
}
