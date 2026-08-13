"use client";

import Link from "next/link";
import { Cpu, ArrowRight, Github, Twitter, ExternalLink } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";

export function LandingFooter() {
  return (
    <footer className="relative bg-background dark:bg-[#090B0F] border-t border-border overflow-hidden transition-colors duration-300">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border)/0.4)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.4)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:linear-gradient(to_bottom,transparent,black)] opacity-10 pointer-events-none" />

      {/* Newsletter Section */}
      <div className="relative border-b border-border py-14 sm:py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h3 className="text-2xl sm:text-3xl font-bold text-foreground mb-3 sm:mb-4 tracking-tight">
              Subscribe to ASEP Updates
            </h3>
            <p className="text-muted-foreground mb-6 sm:mb-8 text-sm sm:text-base max-w-lg mx-auto">
              Get the latest on autonomous engineering, product updates, and early access features.
            </p>
            <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto" onSubmit={(e) => e.preventDefault()}>
              <input 
                type="email" 
                placeholder="Enter your work email" 
                className="flex-1 bg-card border border-border rounded-xl px-4 py-2.5 text-foreground text-sm focus:outline-none focus:border-[#22D3EE] focus:ring-1 focus:ring-[#22D3EE] transition-colors placeholder:text-muted-foreground min-h-[44px]"
                required
              />
              <Button type="submit" className="bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] transition-all font-mono font-bold text-xs rounded-xl min-h-[44px]">
                Subscribe <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </form>
          </div>
        </div>
      </div>

      <div className="relative container mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-10 lg:gap-8">
          
          {/* Brand Column */}
          <div className="lg:col-span-2 flex flex-col items-start">
            <Link href="/" className="flex items-center gap-2.5 mb-4 group min-h-[44px]">
              <div className="p-1.5 bg-gradient-to-br from-[#22D3EE] to-[#2DD4A3] rounded-lg shadow-sm">
                <Cpu className="w-5 h-5 text-[#090B0F]" />
              </div>
              <span className="text-xl font-bold text-foreground tracking-tight font-sans">ASEP</span>
            </Link>
            <p className="text-muted-foreground text-sm leading-relaxed mb-6 max-w-xs">
              Enterprise-grade autonomous engineering agents. Secure by design, built for the teams that ship.
            </p>
            <div className="flex items-center gap-3">
              <Button asChild variant="outline" size="sm" className="border-border text-foreground hover:bg-accent transition-colors rounded-xl min-h-[40px]">
                <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank" rel="noopener noreferrer">
                  <Github className="w-4 h-4 mr-2" />
                  Star on GitHub
                </Link>
              </Button>
              <Link
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2.5 text-muted-foreground hover:text-primary transition-colors border border-border rounded-xl hover:bg-accent min-h-[40px] min-w-[40px] flex items-center justify-center"
              >
                <Twitter className="w-4 h-4" />
                <span className="sr-only">Twitter</span>
              </Link>
            </div>
          </div>

          {/* Product */}
          <div className="lg:col-span-1">
            <h4 className="text-foreground font-semibold mb-4 text-sm tracking-wide">Product</h4>
            <ul className="space-y-3 text-sm">
              {[
                { name: 'Platform', href: '/platform' },
                { name: 'Architecture', href: '/architecture' },
                { name: 'Pricing', href: '/pricing' }
              ].map((item) => (
                <li key={item.name}>
                  <Link href={item.href} className="text-muted-foreground hover:text-foreground transition-colors relative group overflow-hidden pb-0.5 inline-block">
                    {item.name}
                    <span className="absolute bottom-0 left-0 w-full h-px bg-[#22D3EE] translate-x-[-101%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div className="lg:col-span-1">
            <h4 className="text-foreground font-semibold mb-4 text-sm tracking-wide">Resources</h4>
            <ul className="space-y-3 text-sm">
              {[
                { name: 'Documentation', href: '/documentation' },
                { name: 'Roadmap', href: '/roadmap' },
                { name: 'Changelog', href: '/changelog' }
              ].map((item) => (
                <li key={item.name}>
                  <Link href={item.href} className="text-muted-foreground hover:text-foreground transition-colors relative group overflow-hidden pb-0.5 inline-block">
                    {item.name}
                    <span className="absolute bottom-0 left-0 w-full h-px bg-[#22D3EE] translate-x-[-101%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Developers */}
          <div className="lg:col-span-1">
            <h4 className="text-foreground font-semibold mb-4 text-sm tracking-wide">Developers</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/api-docs" className="text-muted-foreground hover:text-foreground transition-colors relative group overflow-hidden pb-0.5 inline-block">
                  API Docs
                  <span className="absolute bottom-0 left-0 w-full h-px bg-[#22D3EE] translate-x-[-101%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
                </Link>
              </li>
              <li>
                <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors inline-flex items-center gap-1 group pb-0.5">
                  GitHub <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div className="lg:col-span-1">
            <h4 className="text-foreground font-semibold mb-4 text-sm tracking-wide">Legal</h4>
            <ul className="space-y-3 text-sm">
              {['About', 'Contact', 'Privacy', 'Terms'].map((item) => (
                <li key={item}>
                  <Link href={`/${item.toLowerCase()}`} className="text-muted-foreground hover:text-foreground transition-colors relative group overflow-hidden pb-0.5 inline-block">
                    {item}
                    <span className="absolute bottom-0 left-0 w-full h-px bg-[#22D3EE] translate-x-[-101%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

        </div>
      </div>

      {/* Bottom Bar */}
      <div className="relative border-t border-border bg-background/80 dark:bg-[#090B0F]/80 backdrop-blur-sm z-10">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-xs sm:text-sm text-muted-foreground">
            <span>© {new Date().getFullYear()} ASEP, Inc.</span>
            <span className="hidden sm:inline w-px h-4 bg-border" />
            <div className="flex items-center gap-2 group">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2DD4A3] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#2DD4A3]" />
              </span>
              <span className="group-hover:text-foreground transition-colors">All Systems Operational</span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-muted-foreground bg-muted/60 px-2.5 py-1 rounded-lg border border-border">
              v0.1.0
            </span>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </footer>
  );
}
