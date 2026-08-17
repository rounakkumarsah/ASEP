import type { NextConfig } from "next";
import "./src/lib/config/env";

/**
 * ASEP — Next.js Configuration
 *
 * TODO (Phase 0.2):
 *   - Add API proxy rewrites (avoid CORS in dev)
 *   - Add image domain allowlist (Ollama model icons, etc.)
 *   - Add bundle analyser
 *   - Configure CSP headers
 */
const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy",
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com https://checkout.razorpay.com https://us.i.posthog.com https://us-assets.i.posthog.com https://vercel.live; frame-src 'self' https://challenges.cloudflare.com https://api.razorpay.com https://vercel.live; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' data:; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 https: https://us.i.posthog.com https://us-assets.i.posthog.com https://vercel.live;",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
