'use client';

import Link from 'next/link';
import { Cpu, ArrowRight, Github, Twitter, ExternalLink } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Button } from '@/components/ui/button';

export function LandingFooter() {
  return (
    <footer className="relative bg-[#090B0F] border-t border-[#202833] overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#202833_1px,transparent_1px),linear-gradient(to_bottom,#202833_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:linear-gradient(to_bottom,transparent,black)] opacity-10 pointer-events-none" />

      {/* Newsletter Section */}
      <div className="relative border-b border-[#202833] py-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h3 className="text-2xl font-bold text-[#F5F7FA] mb-4">Subscribe to ASEP Updates</h3>
            <p className="text-[#9CA6B5] mb-8">Get the latest on autonomous engineering, product updates, and early access features.</p>
            <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto" onSubmit={(e) => e.preventDefault()}>
              <input 
                type="email" 
                placeholder="Enter your email" 
                className="flex-1 bg-[#0D1117] border border-[#202833] rounded-md px-4 py-2 text-[#F5F7FA] focus:outline-none focus:border-[#22D3EE] focus:ring-1 focus:ring-[#22D3EE] transition-colors placeholder:text-[#667085]"
                required
              />
              <Button type="submit" className="bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] transition-colors font-semibold">
                Subscribe <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </form>
          </div>
        </div>
      </div>

      <div className="relative container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-12 lg:gap-8">
          
          {/* Brand Column */}
          <div className="lg:col-span-2 flex flex-col items-start">
            <Link href="/" className="flex items-center gap-2 mb-4 group">
              <div className="p-1.5 bg-[#111720] rounded-md border border-[#202833] group-hover:border-[#22D3EE]/50 transition-colors">
                <Cpu className="w-6 h-6 text-[#22D3EE]" />
              </div>
              <span className="text-xl font-bold text-[#F5F7FA] tracking-tight">ASEP</span>
            </Link>
            <p className="text-[#9CA6B5] text-sm leading-relaxed mb-6 max-w-xs">
              Enterprise-grade autonomous engineering agents. Secure by design, built for the teams that ship.
            </p>
            <div className="flex items-center gap-4">
              <Button asChild variant="outline" size="sm" className="bg-[#0D1117] border-[#202833] text-[#F5F7FA] hover:bg-[#111720] hover:text-[#22D3EE] transition-colors">
                <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank" rel="noopener noreferrer">
                  <Github className="w-4 h-4 mr-2" />
                  Star on GitHub
                </Link>
              </Button>
              <Link href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="p-2 text-[#9CA6B5] hover:text-[#22D3EE] transition-colors bg-[#0D1117] border border-[#202833] rounded-md hover:bg-[#111720]">
                <Twitter className="w-4 h-4" />
                <span className="sr-only">Twitter</span>
              </Link>
            </div>
          </div>

          {/* Product */}
          <div className="lg:col-span-1">
            <h4 className="text-[#F5F7FA] font-semibold mb-6">Product</h4>
            <ul className="space-y-4 text-sm">
              {['Platform', 'Architecture', 'Pricing'].map((item) => (
                <li key={item}>
                  <Link href={`/${item.toLowerCase()}`} className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors relative group overflow-hidden pb-1 inline-block">
                    {item}
                    <span className="absolute bottom-0 left-0 w-full h-px bg-[#22D3EE] translate-x-[-101%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div className="lg:col-span-1">
            <h4 className="text-[#F5F7FA] font-semibold mb-6">Resources</h4>
            <ul className="space-y-4 text-sm">
              {[
                { name: 'Documentation', path: '/documentation' },
                { name: 'Roadmap', path: '/roadmap' },
                { name: 'Changelog', path: '/changelog' },
              ].map((item) => (
                <li key={item.name}>
                  <Link href={item.path} className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors relative group overflow-hidden pb-1 inline-block">
                    {item.name}
                    <span className="absolute bottom-0 left-0 w-full h-px bg-[#22D3EE] translate-x-[-101%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Developers */}
          <div className="lg:col-span-1">
            <h4 className="text-[#F5F7FA] font-semibold mb-6">Developers</h4>
            <ul className="space-y-4 text-sm">
              <li>
                <Link href="/api-docs" className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors relative group overflow-hidden pb-1 inline-block">
                  API Docs
                  <span className="absolute bottom-0 left-0 w-full h-px bg-[#22D3EE] translate-x-[-101%] group-hover:translate-x-0 transition-transform duration-300 ease-out" />
                </Link>
              </li>
              <li>
                <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank" rel="noopener noreferrer" className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors inline-flex items-center gap-1 group pb-1">
                  GitHub <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div className="lg:col-span-1">
            <h4 className="text-[#F5F7FA] font-semibold mb-6">Legal</h4>
            <ul className="space-y-4 text-sm">
              {['About', 'Contact', 'Privacy', 'Terms'].map((item) => (
                <li key={item}>
                  <Link href={`/${item.toLowerCase()}`} className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors relative group overflow-hidden pb-1 inline-block">
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
      <div className="relative border-t border-[#202833] bg-[#090B0F]/80 backdrop-blur-sm z-10">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-sm text-[#667085]">
            <span>© {new Date().getFullYear()} ASEP, Inc.</span>
            <span className="hidden sm:inline w-px h-4 bg-[#202833]" />
            <div className="flex items-center gap-2 group">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2DD4A3] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#2DD4A3]"></span>
              </span>
              <span className="group-hover:text-[#F5F7FA] transition-colors">All Systems Operational</span>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <span className="text-sm font-mono text-[#667085] bg-[#111720] px-2 py-1 rounded border border-[#202833]">
              ASEP v0.1.0
            </span>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </footer>
  );
}
