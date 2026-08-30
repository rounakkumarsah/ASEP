"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2, MailCheck, RotateCcw, ExternalLink, ArrowLeft, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { GuestRoute } from "@/components/auth/guest-route";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const token = searchParams.get("token") || "";
  const [code, setCode] = React.useState("");
  const [verifying, setVerifying] = React.useState(false);
  const [resending, setResending] = React.useState(false);
  const [resendCooldown, setResendCooldown] = React.useState(0);
  const [resendMsg, setResendMsg] = React.useState("");
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState("");

  // Cooldown countdown timer
  React.useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleVerify = React.useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setVerifying(true);
    setError("");
    setResendMsg("");
    const API_URL = "";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/verify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          token ? { token } : { email: email.trim().toLowerCase(), code: code.trim() }
        ),
      });

      if (!res.ok) {
        const errData = await res.json();
        setError(errData.detail || "Invalid or expired verification code.");
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
    if (!email || resending || resendCooldown > 0) return;
    setResending(true);
    setResendMsg("");
    setError("");
    const API_URL = "";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        setResendMsg("A new verification code has been dispatched to your inbox.");
        setResendCooldown(60);
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
      <div className="w-full flex items-center justify-center p-4">
        <Card className="w-full max-w-md border border-[#202833] bg-[#0D1117] shadow-2xl text-center rounded-2xl">
          <CardHeader className="pb-4 pt-8">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#22D3EE]/10 border border-[#22D3EE]/20 text-[#22D3EE] shadow-inner">
              <MailCheck className="h-7 w-7" />
            </div>
            <CardTitle className="text-2xl font-bold font-mono tracking-tight text-[#F5F7FA]">
              Verify your email
            </CardTitle>
            <CardDescription className="text-xs text-[#9CA6B5] font-sans pt-2 px-2 leading-relaxed">
              We sent a verification link and 6-digit code to
              <br />
              <span className="inline-block mt-1 font-mono font-semibold text-[#22D3EE] bg-[#22D3EE]/10 px-2 py-0.5 rounded border border-[#22D3EE]/20">
                {email || "your email address"}
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 px-6 pb-8">
            {error && (
              <div className="p-3 text-xs font-mono text-[#F05252] bg-[#F05252]/10 rounded-xl border border-[#F05252]/20">
                {error}
              </div>
            )}
            {resendMsg && (
              <div className="p-3 text-xs font-mono text-[#22D3EE] bg-[#22D3EE]/10 rounded-xl border border-[#22D3EE]/20">
                ✓ {resendMsg}
              </div>
            )}
            {success ? (
              <div className="p-4 text-xs font-mono text-[#2DD4A3] bg-[#2DD4A3]/10 rounded-xl border border-[#2DD4A3]/20 flex items-center justify-center gap-2">
                <span className="text-base">✓</span> Email verified successfully! Redirecting to login...
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-2.5 pt-1">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => window.open("https://mail.google.com", "_blank")}
                    className="h-10 text-xs font-mono border-[#202833] bg-[#111720] hover:bg-[#161f2e] text-[#F5F7FA] flex items-center justify-center gap-1.5 rounded-xl"
                  >
                    <Mail className="w-3.5 h-3.5 text-[#F5B942]" />
                    Open Gmail
                    <ExternalLink className="w-3 h-3 text-[#667085]" />
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => window.open("https://outlook.live.com", "_blank")}
                    className="h-10 text-xs font-mono border-[#202833] bg-[#111720] hover:bg-[#161f2e] text-[#F5F7FA] flex items-center justify-center gap-1.5 rounded-xl"
                  >
                    <Mail className="w-3.5 h-3.5 text-[#38BDF8]" />
                    Open Outlook
                    <ExternalLink className="w-3 h-3 text-[#667085]" />
                  </Button>
                </div>

                <div className="relative flex py-1 items-center">
                  <div className="flex-grow border-t border-[#202833]"></div>
                  <span className="flex-shrink mx-3 text-[11px] font-mono text-[#667085] uppercase">
                    or enter 6-digit code
                  </span>
                  <div className="flex-grow border-t border-[#202833]"></div>
                </div>

                <form onSubmit={handleVerify} className="space-y-4 text-left">
                  {!token && (
                    <div className="space-y-1.5">
                      <Input
                        id="otpCode"
                        type="text"
                        placeholder="• • • • • •"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        maxLength={6}
                        autoFocus
                        className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] text-center font-mono tracking-widest text-lg h-12 rounded-xl focus:border-[#22D3EE]"
                      />
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="w-full text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-11 rounded-xl shadow-lg shadow-[#22D3EE]/10"
                    disabled={verifying || (!email && !token) || (!token && code.length < 6)}
                  >
                    {verifying ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Verifying Code...
                      </>
                    ) : (
                      "Confirm Verification"
                    )}
                  </Button>
                </form>

                <div className="pt-2 flex flex-col items-center gap-3">
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={resending || resendCooldown > 0 || !email}
                    className="text-xs font-mono text-[#22D3EE] hover:underline disabled:text-[#667085] disabled:no-underline flex items-center gap-1.5"
                  >
                    <RotateCcw className={`w-3.5 h-3.5 ${resending ? "animate-spin" : ""}`} />
                    {resendCooldown > 0
                      ? `Resend email in ${resendCooldown}s`
                      : resending
                      ? "Sending code..."
                      : "Didn't receive the email? Resend code"}
                  </button>

                  <div className="flex items-center gap-4 text-xs font-sans text-[#9CA6B5] pt-1">
                    <Link
                      href="/signup"
                      className="text-[#9CA6B5] hover:text-[#F5F7FA] transition flex items-center gap-1"
                    >
                      <ArrowLeft className="w-3 h-3" /> Change email
                    </Link>
                    <span className="text-[#202833]">•</span>
                    <Link href="/login" className="text-[#9CA6B5] hover:text-[#F5F7FA] transition">
                      Back to sign in
                    </Link>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
