import type { Metadata } from "next";
import Script from "next/script";
import "@/app/globals.css";
import { ThemeProvider } from "@/lib/providers/theme-provider";
import { QueryProvider } from "@/lib/providers/query-provider";
import { AuthProvider } from "@/lib/providers/auth-provider";

import { AnalyticsProvider } from "@/lib/providers/analytics-provider";

export const metadata: Metadata = {
  title: "ASEP | Autonomous Software Engineering Platform",
  description: "Production Control Plane Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="font-sans min-h-screen bg-background antialiased"
      >
        <Script
          src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
          strategy="afterInteractive"
        />
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <AuthProvider>
              <AnalyticsProvider>{children}</AnalyticsProvider>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

