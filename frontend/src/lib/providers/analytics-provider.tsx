"use client";

import React, { useEffect } from "react";

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // PostHog SDK Initialization using process.env
    const token =
      process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN || process.env.NEXT_PUBLIC_POSTHOG_KEY;
    const host = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com";

    if (token && typeof window !== "undefined") {
      try {
        const script = document.createElement("script");
        script.src = `${host}/static/array.js`;
        script.async = true;
        script.onload = () => {
          const win = window as unknown as Record<string, unknown>;
          if (win.posthog) {
            (win.posthog as { init?: (t: string, opts: Record<string, unknown>) => void }).init?.(
              token,
              {
                api_host: host,
                autocapture: true,
                capture_pageview: true,
              }
            );
            console.log("PostHog Analytics loaded successfully.");
          }
        };
        document.head.appendChild(script);
      } catch (err) {
        console.warn("PostHog initialization error:", err);
      }
    }
  }, []);

  return <>{children}</>;
}
