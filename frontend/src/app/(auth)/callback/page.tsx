"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/providers/auth-provider";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AuthCallbackPage() {
  const params = useSearchParams();
  const { logout } = useAuth();
  const [status, setStatus] = useState<"loading" | "error">("loading");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const success = params.get("success");
    const error = params.get("error");

    if (error) {
      const messages: Record<string, string> = {
        invalid_state: "Security token expired. Please try again.",
        oauth_failed: "OAuth authentication failed. Please try again.",
        access_denied: "Access was denied. Please try again.",
      };
      setErrorMsg(messages[error] || `Authentication error: ${error}`);
      setStatus("error");
      return;
    }

    if (success === "true") {
      window.location.href = "/overview";
    } else {
      setErrorMsg("Unexpected OAuth callback state.");
      setStatus("error");
    }
  }, [params, logout]);

  if (status === "error") {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#090B0F] px-4">
        <Card className="w-full max-w-sm border border-[#202833] bg-[#0D1117] shadow-xl text-center">
          <CardHeader className="pb-4">
            <div className="mx-auto h-11 w-11 rounded-md bg-[#F05252]/10 border border-[#F05252]/20 flex items-center justify-center text-[#F05252] mb-4">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <CardTitle className="text-lg font-bold font-mono text-[#F5F7FA]">Authentication Failed</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-xs font-mono text-[#9CA6B5]">{errorMsg}</p>
            <Button asChild className="w-full text-xs font-mono font-semibold border-[#202833] bg-[#111720] text-[#F5F7FA] hover:bg-[#1A212D] h-10">
              <Link href="/login">Back to Login</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-[#090B0F]">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-[#22D3EE]" />
        <p className="text-xs font-mono font-bold text-[#F5F7FA] tracking-widest uppercase">Completing Sign In...</p>
      </div>
    </div>
  );
}
