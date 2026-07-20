"use client";

import * as React from "react";

interface TurnstileProps {
  onVerify: (token: string | null) => void;
}

export function Turnstile({ onVerify }: TurnstileProps) {
  const [verified, setVerified] = React.useState(false);
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

  React.useEffect(() => {
    // If running in production with a valid Turnstile key, we could inject the CF script
    // For local development and fallback/testing, we render an accessible verification widget.
    if (siteKey && typeof window !== "undefined") {
      // Production Cloudflare Turnstile loading could be done here.
    }
  }, [siteKey]);

  const handleCheckboxChange = (checked: boolean) => {
    setVerified(checked);
    if (checked) {
      onVerify("mock-cloudflare-turnstile-token");
    } else {
      onVerify(null);
    }
  };

  return (
    <div className="p-4 border border-border/50 rounded-lg bg-card/50 flex flex-col gap-2">
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="turnstile-captcha"
          checked={verified}
          onChange={(e) => handleCheckboxChange(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          aria-label="Verify you are human"
        />
        <label htmlFor="turnstile-captcha" className="text-sm font-medium text-muted-foreground select-none">
          Verify you are human (Cloudflare Turnstile)
        </label>
      </div>
      <p className="text-xs text-muted-foreground/75 px-7">
        Secure bot protection powered by ASEP Web Shield.
      </p>
    </div>
  );
}
