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
  // Strict mode enables extra React development warnings
  reactStrictMode: true,

  // TODO (Phase 0.2): add rewrites for API proxy
  // async rewrites() {
  //   return [
  //     {
  //       source: "/api/:path*",
  //       destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
  //     },
  //   ];
  // },
};

export default nextConfig;
