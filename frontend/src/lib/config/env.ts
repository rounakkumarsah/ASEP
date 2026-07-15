import { z } from "zod";

const envSchema = z.object({
  // Server-side only (never exposed to client bundle)
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  
  // Client-side (exposed via NEXT_PUBLIC_ prefix)
  NEXT_PUBLIC_API_URL: z.string().url("NEXT_PUBLIC_API_URL must be a valid URL").default("http://localhost:8000"),
});

const _env = envSchema.safeParse({
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
});

if (!_env.success) {
  console.error("❌ Invalid environment variables:", _env.error.format());
  process.exit(1);
}

export const env = _env.data;
