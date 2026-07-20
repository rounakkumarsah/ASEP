"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Hexagon, MailCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { GuestRoute } from "@/components/auth/guest-route";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const [verifying, setVerifying] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState("");

  const handleVerify = async () => {
    setVerifying(true);
    setError("");
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/verify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          code: "123456", // Default mock code configured on backend
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        setError(errData.detail || "Invalid or expired verification code.");
        setVerifying(false);
        return;
      }

      setVerifying(false);
      setSuccess(true);
      localStorage.setItem("asep_email_verified", "true");
      setTimeout(() => {
        router.push("/login?verified=true");
      }, 1500);
    } catch {
      setError("Unable to connect to the authentication server.");
      setVerifying(false);
    }
  };

  return (
    <GuestRoute>
      <div className="flex h-screen w-full items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md border border-border/50 bg-card shadow-lg text-center">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Hexagon className="h-10 w-10 text-primary animate-pulse" />
              <span className="text-2xl font-bold tracking-tight">ASEP</span>
            </div>
            <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
              <MailCheck className="h-6 w-6" />
            </div>
            <CardTitle className="text-2xl font-bold">Verify Your Email</CardTitle>
            <CardDescription className="pt-2">
              We sent a verification link to <span className="font-semibold text-foreground">{email || "your email address"}</span>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg border border-destructive/20 font-semibold">
                {error}
              </div>
            )}
            {success ? (
              <div className="p-3 text-sm text-green-600 bg-green-500/10 rounded-lg border border-green-500/20 font-semibold">
                Account activated! Redirecting to sign in...
              </div>
            ) : (
              <Button
                onClick={handleVerify}
                className="w-full font-semibold"
                disabled={verifying || !email}
              >
                {verifying ? "Activating Account..." : "Activate Account"}
              </Button>
            )}
            <div className="text-xs text-muted-foreground pt-4">
              Didn&apos;t receive the email?{" "}
              <button
                onClick={() => alert("Verification code is '123456'. Click Activate Account.")}
                className="font-semibold text-primary hover:underline"
              >
                Show validation code
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
