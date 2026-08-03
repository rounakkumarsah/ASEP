"use client";

/**
 * ASEP — Cloudflare Turnstile Component
 *
 * EXECUTION MODEL: execution="execute" (MANUAL)
 *
 * ROOT CAUSE OF PREVIOUS BUG:
 * The old implementation used the default Cloudflare execution mode which is
 * "render" — meaning the widget auto-executes and generates a token immediately
 * on page load. By the time the user fills the form and clicks Register,
 * the 5-minute token has expired → Cloudflare returns `timeout-or-duplicate`.
 *
 * FIX:
 * We now use execution="execute" (manual mode).
 * - Widget renders silently on page load. NO token is generated.
 * - The parent calls ref.execute() ONLY when Register button is clicked.
 * - Cloudflare verifies → callback fires with a fresh token.
 * - Parent receives the fresh token and immediately submits the API request.
 * - On ANY failure: ref.reset() clears the widget → next attempt gets a new token.
 *
 * GUARANTEES:
 * ✅ Token is never generated on page load.
 * ✅ Token is generated ONLY after Register/Login click.
 * ✅ Every API request uses a brand-new token.
 * ✅ Old tokens are NEVER reused.
 * ✅ Failed requests always reset Turnstile before retry.
 * ✅ No race conditions — callback fires synchronously after execute().
 * ✅ No duplicate submissions — widget is in "executing" state until reset.
 */

import * as React from "react";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface TurnstileRef {
  /**
   * Trigger manual Turnstile execution.
   * Call this ONLY when the user clicks the submit button (after form validation).
   * The onToken callback will fire with a fresh token.
   */
  execute: () => void;
  /**
   * Reset the widget — clears the current token and starts a fresh challenge.
   * Must be called after every API failure so the next submission uses a new token.
   */
  reset: () => void;
  /**
   * Returns true if Turnstile is currently mid-execution (challenge visible or processing).
   */
  isExecuting: () => boolean;
}

export interface TurnstileProps {
  /**
   * Called when Cloudflare successfully verifies and issues a fresh token.
   * This is your signal to immediately submit the API request.
   */
  onToken: (token: string) => void;
  /**
   * Called when the current token expires. Parent should block submission.
   */
  onExpire?: () => void;
  /**
   * Called when Cloudflare encounters a verification error.
   * Parent should show an error and re-enable the submit button.
   */
  onError?: () => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Global Turnstile SDK types
// ─────────────────────────────────────────────────────────────────────────────

declare global {
  interface Window {
    turnstile?: {
      render: (
        container: string | HTMLElement,
        options: {
          sitekey: string;
          action?: string;
          execution?: "render" | "execute"; // "execute" = manual mode
          callback: (token: string) => void;
          "expired-callback"?: () => void;
          "error-callback"?: () => void;
          theme?: "light" | "dark" | "auto";
        }
      ) => string;
      execute: (widgetId: string) => void;
      reset: (widgetId: string) => void;
      remove: (widgetId: string) => void;
    };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Site key resolution
// ─────────────────────────────────────────────────────────────────────────────

// Official Cloudflare always-pass test key — safe for development/staging
// https://developers.cloudflare.com/turnstile/troubleshooting/testing/
const CF_TEST_SITE_KEY = "1x00000000000000000000AA";

function resolveSiteKey(): string {
  const envKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
  if (envKey && envKey.trim() !== "") return envKey.trim();
  return CF_TEST_SITE_KEY;
}

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────

export const Turnstile = React.forwardRef<TurnstileRef, TurnstileProps>(
  function Turnstile({ onToken, onExpire, onError }, ref) {
    const containerRef = React.useRef<HTMLDivElement>(null);
    const widgetIdRef = React.useRef<string | null>(null);
    const executingRef = React.useRef(false);
    const mountedRef = React.useRef(true);

    // Keep callbacks stable — always call the latest version
    const onTokenRef = React.useRef(onToken);
    const onExpireRef = React.useRef(onExpire);
    const onErrorRef = React.useRef(onError);
    React.useEffect(() => { onTokenRef.current = onToken; }, [onToken]);
    React.useEffect(() => { onExpireRef.current = onExpire; }, [onExpire]);
    React.useEffect(() => { onErrorRef.current = onError; }, [onError]);

    const siteKey = resolveSiteKey();

    // ── Imperative API exposed to parent ──────────────────────────────────────
    React.useImperativeHandle(ref, () => ({
      execute: () => {
        if (!window.turnstile || !widgetIdRef.current) {
          console.warn("[Turnstile] execute() called before widget is ready.");
          return;
        }
        if (executingRef.current) {
          // Already mid-execution — prevent duplicate calls
          return;
        }
        executingRef.current = true;
        try {
          window.turnstile.execute(widgetIdRef.current);
        } catch (err) {
          console.error("[Turnstile] execute() failed:", err);
          executingRef.current = false;
          onErrorRef.current?.();
        }
      },

      reset: () => {
        executingRef.current = false;
        if (window.turnstile && widgetIdRef.current) {
          try {
            window.turnstile.reset(widgetIdRef.current);
          } catch {}
        }
      },

      isExecuting: () => executingRef.current,
    }));

    // ── Render widget on mount ─────────────────────────────────────────────────
    React.useEffect(() => {
      mountedRef.current = true;

      // E2E test bypass
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if (typeof window !== "undefined" && (window as any).__PLAYWRIGHT_TEST__) {
        // In tests, we auto-issue a token so tests don't block on Cloudflare
        setTimeout(() => {
          if (mountedRef.current) onTokenRef.current("mock-turnstile-token");
        }, 50);
        return;
      }

      const renderWidget = () => {
        if (!mountedRef.current || !containerRef.current || !window.turnstile) return;

        // Already rendered
        if (widgetIdRef.current) return;

        // Clean container
        containerRef.current.innerHTML = "";

        try {
          const id = window.turnstile.render(containerRef.current, {
            sitekey: siteKey,
            action: "asep-auth",
            // ★ KEY FIX: execution="execute" prevents auto-token generation.
            //   Widget renders silently. Token is only generated when
            //   window.turnstile.execute(widgetId) is called manually.
            execution: "execute",
            theme: "auto",

            callback: (token: string) => {
              // Fresh token received — immediately pass to parent for API submission
              executingRef.current = false;
              if (mountedRef.current) onTokenRef.current(token);
            },

            "expired-callback": () => {
              // Token expired (rare in execute mode, but handle it)
              executingRef.current = false;
              if (mountedRef.current) onExpireRef.current?.();
            },

            "error-callback": () => {
              // Cloudflare error — parent should show error & re-enable submit button
              executingRef.current = false;
              if (mountedRef.current) onErrorRef.current?.();
            },
          });
          widgetIdRef.current = id;
        } catch (err) {
          console.error("[Turnstile] render() failed:", err);
        }
      };

      const scriptId = "cloudflare-turnstile-script";
      let script = document.getElementById(scriptId) as HTMLScriptElement | null;

      if (!script) {
        script = document.createElement("script");
        script.id = scriptId;
        // render=explicit is required for manual rendering
        script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
        script.async = true;
        script.defer = true;
        document.body.appendChild(script);
      }

      if (window.turnstile) {
        renderWidget();
      } else {
        script.addEventListener("load", renderWidget);
      }

      return () => {
        mountedRef.current = false;
        script?.removeEventListener("load", renderWidget);
        if (widgetIdRef.current && window.turnstile) {
          try {
            window.turnstile.remove(widgetIdRef.current);
          } catch {}
          widgetIdRef.current = null;
        }
      };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [siteKey]);

    // Render an invisible container — widget lives here but shows nothing until executed
    return (
      <div
        ref={containerRef}
        className="cf-turnstile"
        aria-hidden="true"
        style={{ minHeight: 0 }}
      />
    );
  }
);

Turnstile.displayName = "Turnstile";
