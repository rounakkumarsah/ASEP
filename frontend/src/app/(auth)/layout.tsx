"use client";

import * as React from "react";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Cpu } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen w-full bg-[#090B0F] text-[#F5F7FA] flex flex-col justify-center items-center p-6 sm:p-10">
      
      {/* Background patterns/glows */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#111720_1px,transparent_1px),linear-gradient(to_bottom,#111720_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-50 pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-[#22D3EE]/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Floating Theme Toggle in Top Right */}
      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Brand Logo at the top */}
      <div className="mb-10 z-10 flex flex-col items-center">
        <Link href="/" className="flex items-center space-x-2.5 group">
          <div className="p-1.5 rounded-lg bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/50 transition-colors shadow-sm">
            <Cpu className="h-5 w-5" />
          </div>
          <span className="font-mono font-bold tracking-wider text-lg">ASEP</span>
        </Link>
      </div>

      {/* Sleek card container wrapper */}
      <div className="w-full max-w-md z-10">
        {children}
      </div>

      {/* Footer copyright */}
      <div className="mt-12 text-xs font-mono text-[#667085] z-10">
        &copy; {new Date().getFullYear()} ASEP Inc.
      </div>
    </div>
  );
}
