import { z } from "zod";

const envSchema = z.object({
  // Server-side only (never exposed to client bundle)
  NODE_ENV: z
    .enum(["development", "test", "production"])
    .default("development"),

  // Client-side (exposed via NEXT_PUBLIC_ prefix)
  NEXT_PUBLIC_API_URL: z
    .string()
    .url("NEXT_PUBLIC_API_URL must be a valid URL")
    .default("http://localhost:8000"),

  NEXT_PUBLIC_ENABLE_TURNSTILE: z
    .preprocess(
      (val) => {
        if (typeof val === "string") return val.toLowerCase() !== "false";
        if (typeof val === "boolean") return val;
        return true;
      },
      z.boolean()
    )
    .default(true),

  // Cloudflare Turnstile — site key for the human verification widget.
  // Required in production. In development/CI, Cloudflare test keys are used
  // automatically by the Turnstile component when this is absent.
  NEXT_PUBLIC_TURNSTILE_SITE_KEY: z
    .string()
    .optional(),

  // Application environment override (used by the Turnstile component to
  // distinguish production from local dev even inside Docker).
  NEXT_PUBLIC_APP_ENV: z
    .enum(["development", "staging", "production"])
    .default("development"),

  // Razorpay — public Key ID only. The Key Secret stays server-side.
  NEXT_PUBLIC_RAZORPAY_KEY_ID: z
    .string()
    .optional()
    .describe("Razorpay Key ID. Use rzp_test_* in test mode and rzp_live_* in live mode."),
});

const _env = envSchema.safeParse({
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_ENABLE_TURNSTILE: process.env.NEXT_PUBLIC_ENABLE_TURNSTILE,
  NEXT_PUBLIC_TURNSTILE_SITE_KEY: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY,
  NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
  NEXT_PUBLIC_RAZORPAY_KEY_ID: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
});

if (!_env.success) {
  console.error("❌ Invalid environment variables:", _env.error.format());
  process.exit(1);
}

const parsed = _env.data;

// Fail-fast: in production, NEXT_PUBLIC_TURNSTILE_SITE_KEY must be set if enabled.
if (
  (parsed.NODE_ENV === "production" || parsed.NEXT_PUBLIC_APP_ENV === "production") &&
  parsed.NEXT_PUBLIC_ENABLE_TURNSTILE &&
  !parsed.NEXT_PUBLIC_TURNSTILE_SITE_KEY
) {
  console.error(
    "❌ Missing required environment variable: NEXT_PUBLIC_TURNSTILE_SITE_KEY\n" +
    "   This variable must be set in Vercel Environment Variables for production deployments."
  );
  // In browser context process.exit is unavailable — the Turnstile component
  // handles the UI error; here we only log the configuration problem.
}

export const env = parsed;
