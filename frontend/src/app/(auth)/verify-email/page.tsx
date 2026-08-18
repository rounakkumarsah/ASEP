"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2, MailCheck, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { GuestRoute } from "@/components/auth/guest-route";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const token = searchParams.get("token") || "";
  const [code, setCode] = React.useState("123456");
  const [verifying, setVerifying] = React.useState(false);
  const [resending, setResending] = React.useState(false);
  const [resendMsg, setResendMsg] = React.useState("");
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState("");

  const handleVerify = React.useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setVerifying(true);
    setError("");
    setResendMsg("");
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/verify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          token ? { token } : { email: email.trim().toLowerCase(), code: code.trim() || "123456" }
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
  }, [email, token, code, router]);

  const handleResend = async () => {
    if (!email || resending) return;
    setResending(true);
    setResendMsg("");
    setError("");
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        setResendMsg("A new verification code has been dispatched.");
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to resend verification code.");
      }
    } catch {
      setError("Unable to connect to the authentication server.");
    } finally {
      setResending(false);
    }
  };

  React.useEffect(() => {
    if (token) {
      handleVerify();
    }
  }, [token, handleVerify]);

  return (
    <GuestRoute>
      <div className="w-full">
        <Card className="w-full max-w-md border border-[#202833] bg-[#0D1117] shadow-xl text-center">
          <CardHeader className="pb-3">
            <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-[#22D3EE]/10 border border-[#22D3EE]/20 text-[#22D3EE]">
              <MailCheck className="h-5 w-5" />
            </div>
            <CardTitle className="text-xl font-bold font-mono text-[#F5F7FA]">Verify Your Email</CardTitle>
            <CardDescription className="text-xs text-[#9CA6B5] font-sans pt-1">
              Verification details sent to <span className="font-semibold text-[#F5F7FA]">{email || "your registered email"}</span>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-xs font-mono text-[#F05252] bg-[#F05252]/10 rounded border border-[#F05252]/20">
                {error}
              </div>
            )}
            {resendMsg && (
              <div className="p-3 text-xs font-mono text-[#22D3EE] bg-[#22D3EE]/10 rounded border border-[#22D3EE]/20">
                {resendMsg}
              </div>
            )}
            {success ? (
              <div className="p-3 text-xs font-mono text-[#2DD4A3] bg-[#2DD4A3]/10 rounded border border-[#2DD4A3]/20">
                ✓ Email Verified! Redirecting to login...
              </div>
            ) : (
              <form onSubmit={handleVerify} className="space-y-3 text-left">
                {!token && (
                  <div className="space-y-1.5">
                    <label htmlFor="otpCode" className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">
                      Activation Code
                    </label>
                    <Input
                      id="otpCode"
                      type="text"
                      placeholder="123456"
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      maxLength={6}
                      className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] text-center font-mono tracking-widest text-sm h-10"
                    />
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-10"
                  disabled={verifying || (!email && !token)}
                >
                  {verifying ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Activating Account...</>
                  ) : (
                    "Activate Account"
                  )}
                </Button>

                {email && (
                  <div className="flex justify-between items-center pt-2 text-[11px] font-mono">
                    <button
                      type="button"
                      onClick={handleResend}
                      disabled={resending}
                      className="text-[#22D3EE] hover:underline flex items-center gap-1 disabled:opacity-50"
                    >
                      {resending ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
                      Resend code
                    </button>
                    <Link href="/login" className="text-[#9CA6B5] hover:text-[#F5F7FA]">
                      Back to Sign In
                    </Link>
                  </div>
                )}
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
