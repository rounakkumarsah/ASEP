'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowRight, BookOpen, Terminal, Copy, ShieldCheck, Zap, Clock, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CTASection() {
  const [copied, setCopied] = useState(false);

  const copyCommand = () => {
    navigator.clipboard.writeText('npx asep-cli init --secure --local');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative w-full overflow-hidden bg-background dark:bg-[#090B0F] py-24 sm:py-32 border-t border-border transition-colors duration-300">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-[1000px] h-[500px] bg-[#22D3EE]/20 blur-[120px] rounded-full pointer-events-none opacity-50 mix-blend-screen" />
        {/* CSS Noise */}
        <div 
          className="absolute inset-0 opacity-[0.03] pointer-events-none mix-blend-overlay" 
          style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}
        />
        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border)/0.4)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.4)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20" />
      </div>

      <div className="container relative z-10 mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground mb-6">
              Deploy Autonomous Engineering Agents <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#22D3EE] to-[#2DD4A3]">Into Production</span>
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-muted-foreground mb-10 sm:mb-12 max-w-2xl mx-auto leading-relaxed">
              Enterprise-grade. Secure by design. Built for the teams that ship.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Button asChild size="lg" className="w-full sm:w-auto bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] hover:shadow-[0_0_20px_rgba(34,211,238,0.4)] transition-all duration-300 relative overflow-hidden group border-none">
              <Link href="/signup">
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
                <span className="relative flex items-center gap-2 font-semibold">
                  Start for Free
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>
            </Button>
            
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto bg-transparent border-[#202833] text-[#F5F7FA] hover:bg-[#111720] hover:border-[#22D3EE]/50 hover:shadow-[0_0_15px_rgba(34,211,238,0.15)] transition-all duration-300 group">
              <Link href="/contact">
                <span className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-[#9CA6B5] group-hover:text-[#22D3EE] transition-colors" />
                  Book a Demo
                </span>
              </Link>
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="flex flex-wrap items-center justify-center gap-6 sm:gap-12 mb-16"
          >
            {[
              { icon: ShieldCheck, text: "SOC2 Ready" },
              { icon: Zap, text: "Air-Gap Support" },
              { icon: Clock, text: "<15ms Latency" }
            ].map((badge, idx) => (
              <div key={idx} className="flex items-center gap-2 text-[#9CA6B5]">
                <div className="p-2 rounded-full bg-[#111720] border border-[#202833]">
                  <badge.icon className="w-4 h-4 text-[#2DD4A3]" />
                </div>
                <span className="text-sm font-medium">{badge.text}</span>
              </div>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="max-w-md mx-auto"
          >
            <div className="flex items-center justify-between bg-[#0D1117] border border-[#202833] rounded-lg p-3 group hover:border-[#202833]/80 transition-colors relative overflow-hidden shadow-lg shadow-black/20">
              <div className="absolute top-0 left-0 w-1 h-full bg-[#22D3EE]" />
              <div className="flex items-center gap-3 pl-2">
                <Terminal className="w-5 h-5 text-[#667085]" />
                <code className="text-sm text-[#F5F7FA] font-mono">
                  <span className="text-[#2DD4A3]">npx</span> asep-cli init <span className="text-[#9CA6B5]">--secure --local</span>
                </code>
              </div>
              <button 
                onClick={copyCommand}
                className="p-2 hover:bg-[#111720] rounded-md transition-colors text-[#9CA6B5] hover:text-[#F5F7FA]"
                aria-label="Copy command"
              >
                {copied ? <Check className="w-4 h-4 text-[#2DD4A3]" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
