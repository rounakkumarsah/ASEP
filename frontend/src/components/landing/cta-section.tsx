'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
    <section className="relative w-full overflow-hidden bg-background dark:bg-[#090B0F] py-20 sm:py-28 md:py-32 border-t border-border transition-colors duration-300">
      {/* Background Effects */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-[1000px] h-[500px] bg-[#22D3EE]/20 blur-[120px] rounded-full pointer-events-none opacity-50 mix-blend-screen" />
        {/* CSS Noise */}
        <div 
          className="absolute inset-0 opacity-[0.03] pointer-events-none mix-blend-overlay" 
          style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}
        />
        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border)/0.35)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.35)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20" />
      </div>

      <div className="container relative z-10 mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground mb-4 sm:mb-6">
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
            className="flex flex-col sm:flex-row items-center justify-center gap-3.5 mb-12 sm:mb-16"
          >
            <Button asChild size="lg" className="w-full sm:w-auto bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] hover:shadow-[0_0_24px_rgba(34,211,238,0.45)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 rounded-xl min-h-[44px] px-7 font-mono font-bold text-xs">
              <Link href="/signup">
                <span className="flex items-center gap-2">
                  Start for Free
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
            </Button>
            
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto border-border text-foreground hover:bg-accent hover:border-primary/40 transition-all duration-200 rounded-xl min-h-[44px] px-6 font-mono font-medium text-xs">
              <Link href="/contact">
                <span className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-muted-foreground" />
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
            className="flex flex-wrap items-center justify-center gap-4 sm:gap-8 mb-12 sm:mb-16"
          >
            {[
              { icon: ShieldCheck, text: "SOC2 Ready" },
              { icon: Zap, text: "Air-Gap Support" },
              { icon: Clock, text: "<15ms Latency" }
            ].map((badge, idx) => (
              <div key={idx} className="flex items-center gap-2 text-muted-foreground">
                <div className="p-1.5 sm:p-2 rounded-lg bg-muted/60 dark:bg-[#111720] border border-border/80 dark:border-[#202833]">
                  <badge.icon className="w-3.5 h-3.5 text-[#2DD4A3]" />
                </div>
                <span className="text-xs sm:text-sm font-medium font-mono">{badge.text}</span>
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
            <div className="flex items-center justify-between bg-card dark:bg-[#0D1117] border border-border/80 dark:border-[#202833] rounded-xl p-2.5 sm:p-3 hover:border-primary/40 transition-colors relative overflow-hidden shadow-md">
              <div className="absolute top-0 left-0 w-1 h-full bg-[#22D3EE]" />
              <div className="flex items-center gap-3 pl-2">
                <Terminal className="w-4 h-4 text-muted-foreground" />
                <code className="text-xs sm:text-sm text-foreground font-mono">
                  <span className="text-[#2DD4A3]">npx</span> asep-cli init <span className="text-muted-foreground">--secure --local</span>
                </code>
              </div>
              <button 
                onClick={copyCommand}
                className="p-2 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground min-h-[36px] min-w-[36px] flex items-center justify-center focus-visible:ring-2 focus-visible:ring-primary"
                aria-label="Copy CLI init command"
              >
                <AnimatePresence mode="wait" initial={false}>
                  {copied ? (
                    <motion.div
                      key="check"
                      initial={{ scale: 0.7, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.7, opacity: 0 }}
                      transition={{ duration: 0.15 }}
                    >
                      <Check className="w-4 h-4 text-[#2DD4A3]" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="copy"
                      initial={{ scale: 0.7, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.7, opacity: 0 }}
                      transition={{ duration: 0.15 }}
                    >
                      <Copy className="w-4 h-4" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
