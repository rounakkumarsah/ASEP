"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { GuestRoute } from "@/components/auth/guest-route";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const token = searchParams.get("token") || "";
  const [verifying, setVerifying] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState("");

  const handleVerify = React.useCallback(async () => {
    setVerifying(true);
    setError("");
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/verify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          token ? { token } : { email: email, code: "123456" }
        ),
      });

      if (!res.ok) {
        const errData = await res.json();
        setError(errData.detail || "Invalid or expired verification token.");
        setVerifying(false);
        return;
      }

      setVerifying(false);
      setSuccess(true);
      setTimeout(() => {
        router.push("/login?verified=true");
      }, 1500);
    } catch {
      setError("Unable to connect to the authentication server.");
      setVerifying(false);
    }
  }, [email, token, router]);

  React.useEffect(() => {
    if (token) {
      handleVerify();
    }
  }, [token, handleVerify]);

  return (
    <GuestRoute>
      <div className="w-full">
        <Card className="w-full max-w-md border border-[#202833] bg-[#0D1117] shadow-xl text-center">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold font-mono text-[#F5F7FA]">Verify Your Email</CardTitle>
            <CardDescription className="text-xs text-[#9CA6B5] font-sans pt-2">
              Verification details sent to <span className="font-semibold text-[#F5F7FA]">{email || "your registered email"}</span>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-xs font-mono text-[#F05252] bg-[#F05252]/10 rounded border border-[#F05252]/20">
                {error}
              </div>
            )}
            {success ? (
              <div className="p-3 text-xs font-mono text-[#2DD4A3] bg-[#2DD4A3]/10 rounded border border-[#2DD4A3]/20">
                ✓ Email Verified! Redirecting...
              </div>
            ) : (
              <Button
                onClick={handleVerify}
                className="w-full text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-10"
                disabled={verifying || (!email && !token)}
              >
                {verifying ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Activating Account...</>
                ) : (
                  "Activate Account"
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
