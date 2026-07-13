/**
 * ASEP — Root Layout
 * Scaffold only. TODO (Phase 0.2): implement full layout with sidebar nav.
 */
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ASEP — Autonomous Software Engineering Platform",
  description:
    "Local-first AI engineering operating system. Run autonomous software agents on your own hardware.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
