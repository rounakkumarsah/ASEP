"use client";

import Link from "next/link";
import { Hexagon } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function LandingFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-background border-t border-border/50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-8">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-5 gap-12 lg:gap-8 mb-16">
          {/* Column 1: Brand (Spans 2 on LG) */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center space-x-2 w-fit group">
              <div className="p-1.5 rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
                <Hexagon className="h-6 w-6" />
              </div>
              <span className="text-xl font-bold tracking-tight text-foreground">
                ASEP
              </span>
            </Link>
            <p className="mt-6 text-sm leading-relaxed text-muted-foreground max-w-sm">
              Autonomous Software Engineering Platform. Deploy, monitor, and
              scale enterprise AI agents locally.
            </p>
          </div>

          {/* Column 2: Product */}
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-6">
              Product
            </h3>
            <ul className="space-y-4">
              {[
                { name: "Platform", href: "#platform" },
                { name: "Architecture", href: "#architecture" },
                { name: "Features", href: "#features" },
                { name: "Documentation", href: "/docs" },
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Column 3: Resources */}
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-6">
              Resources
            </h3>
            <ul className="space-y-4">
              {[
                {
                  name: "GitHub",
                  href: "https://github.com/rounakkumarsah/ASEP",
                  external: true,
                },
                { name: "API Documentation", href: "#" },
                { name: "Roadmap", href: "#" },
                { name: "Changelog", href: "#" },
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
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

          {/* Column 4: Company */}
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-6">
              Company
            </h3>
            <ul className="space-y-4">
              {[
                { name: "About", href: "#" },
                { name: "Contact", href: "#" },
                { name: "Privacy Policy", href: "#" },
                { name: "Terms of Service", href: "#" },
              ].map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-border/50 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-col md:flex-row items-center gap-4 text-xs text-muted-foreground">
            <span>&copy; {currentYear} ASEP. All rights reserved.</span>
            <span className="hidden md:inline-block h-1 w-1 rounded-full bg-border" />
            <span>Built with &hearts; using open-source technologies</span>
          </div>
          <div className="flex items-center">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </footer>
  );
}
