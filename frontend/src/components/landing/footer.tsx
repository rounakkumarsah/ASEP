"use client";

import Link from "next/link";
import { Cpu } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function LandingFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#0D1117] border-t border-[#202833] text-[#9CA6B5]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-12 pb-6">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand Info */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center space-x-2.5 group">
              <div className="p-1 rounded bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/50 transition-colors">
                <Cpu className="h-4 w-4" />
              </div>
              <span className="font-mono font-bold tracking-wider text-sm text-[#F5F7FA]">ASEP</span>
            </Link>
            <p className="text-xs leading-relaxed text-[#9CA6B5] max-w-xs font-sans">
              Autonomous Software Engineering Platform. Production-grade multi-agent runtime and workspace sandbox for secure, compliant automation.
            </p>
          </div>

          {/* Column 2: Product */}
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#F5F7FA] mb-4">
              Product
            </h3>
            <ul className="space-y-2.5 text-xs font-mono">
              {[
                { name: "Platform Runtime", href: "/platform" },
                { name: "System Architecture", href: "/architecture" },
                { name: "Pricing Tiers", href: "/pricing" },
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 3: Resources */}
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#F5F7FA] mb-4">
              Resources
            </h3>
            <ul className="space-y-2.5 text-xs font-mono">
              {[
                {
                  name: "GitHub Repository",
                  href: "https://github.com/rounakkumarsah/ASEP",
                  external: true,
                },
                { name: "API Reference Docs", href: "/api-docs" },
                { name: "Documentation Hub", href: "/documentation" },
                { name: "Product Roadmap", href: "/roadmap" },
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors"
                    {...(item.external
                      ? { target: "_blank", rel: "noopener noreferrer" }
                      : {})}
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 4: Trust & Legal */}
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[#F5F7FA] mb-4">
              Company
            </h3>
            <ul className="space-y-2.5 text-xs font-mono">
              {[
                { name: "About ASEP", href: "/about" },
                { name: "Contact Support", href: "/contact" },
                { name: "Privacy Policy", href: "/privacy" },
                { name: "Terms of Service", href: "/terms" },
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-[#202833] flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-[10px] font-mono text-[#667085]">
            <span>&copy; {currentYear} ASEP. All rights reserved.</span>
            <span>•</span>
            <span>Enterprise SLA Active</span>
          </div>
          <div className="flex items-center">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </footer>
  );
}
