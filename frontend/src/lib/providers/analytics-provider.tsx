"use client";

import React, { useEffect } from "react";

let posthogLoaded = false; // Module-level singleton guard

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (posthogLoaded) return; // Already initialized
    
    const token =
      process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN || process.env.NEXT_PUBLIC_POSTHOG_KEY;
    const host = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com";

    if (!token || typeof window === "undefined") return;
    
    posthogLoaded = true;
    
    try {
      const script = document.createElement("script");
      script.src = `${host}/static/array.js`;
      script.async = true;
      script.defer = true; // Add defer for lower priority
      script.onload = () => {
        const win = window as unknown as Record<string, unknown>;
        if (win.posthog) {
          (win.posthog as { init?: (t: string, opts: Record<string, unknown>) => void }).init?.(
            token,
            {
              api_host: host,
              autocapture: true,
              capture_pageview: true,
              loaded: () => {
                // Silent success
              },
            }
          );
        }
      };
      document.head.appendChild(script);
    } catch {
      // Silent failure
    }
  }, []);

  return <>{children}</>;
}
