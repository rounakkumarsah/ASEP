"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/providers/auth-provider";
import Link from "next/link";

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
      <div className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 max-w-md text-center">
          <h2 className="text-lg font-semibold text-red-400 mb-2">Authentication Failed</h2>
          <p className="text-sm text-muted-foreground">{errorMsg}</p>
        </div>
        <Link
          href="/login"
          className="text-sm text-primary hover:underline"
        >
          Back to Login
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      <p className="text-sm text-muted-foreground">Completing sign in...</p>
    </div>
  );
}
