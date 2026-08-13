"use client";

import React, { useState, useEffect } from "react";
import { motion, Variants } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Github,
  Lock,
  Layers,
  Network,
  ShieldCheck,
  BookOpen,
} from "lucide-react";
import dynamic from "next/dynamic";
import { Spotlight } from "@/components/ui/spotlight";
import Marquee from "@/components/ui/marquee";

// Lazy load the high-density interactive control plane demo
const HeroProductDemo = dynamic(
  () => import("@/components/landing/hero-product-demo").then((m) => m.HeroProductDemo),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[460px] rounded-3xl border border-border/80 bg-card/60 backdrop-blur-xl flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
          <span className="text-xs font-mono text-muted-foreground animate-pulse">
            Loading Live Control Plane...
          </span>
        </div>
      </div>
    ),
  }
);

// ── Motion Variants ──────────────────────────────────────────────────────────
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.05 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
};

const letterVariants: Variants = {
  hidden: { opacity: 0, y: 18, rotateX: -30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    rotateX: 0,
    transition: { duration: 0.5, delay: i * 0.03, ease: [0.22, 1, 0.36, 1] },
  }),
};

const autonomousChars = "Autonomous".split("");

export function HeroSection() {
  const fullTagline =
    "Unify Planning, Execution, Memory, and Governance into a single production-grade control plane for autonomous engineering agent collectives.";
  const [typedTagline, setTypedTagline] = useState("");

  useEffect(() => {
    let index = 0;
    const timer = setInterval(() => {
      setTypedTagline(fullTagline.slice(0, index));
      index++;
      if (index > fullTagline.length) clearInterval(timer);
    }, 14);
    return () => clearInterval(timer);
  }, []);

  return (
    <section
      id="hero"
      className="relative min-h-[92vh] overflow-hidden bg-background dark:bg-[#090B0F] pt-24 sm:pt-28 pb-12 sm:pb-16 border-b border-border transition-colors duration-300 flex flex-col justify-center"
    >
      {/* Background Decorative Grids */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-[-100%] bg-[linear-gradient(to_right,hsl(var(--border)/0.35)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.35)_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] opacity-35 dark:opacity-20" />
        <div className="absolute inset-0 bg-background/80 dark:bg-[#090B0F]/80 [mask-image:radial-gradient(ellipse_80%_60%_at_50%_0%,transparent_10%,black_100%)]" />
      </div>

      {/* Radiant Spotlights & Glows */}
      <div className="absolute top-10 left-1/4 w-[550px] h-[550px] bg-[#22D3EE]/10 dark:bg-[#22D3EE]/8 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[450px] h-[450px] bg-[#2DD4A3]/10 dark:bg-[#2DD4A3]/6 rounded-full blur-[140px] pointer-events-none" />
      <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="#22D3EE" />

      {/* Main Container */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          
          {/* ══════════════════ LEFT COLUMN: COPY & VALUE PROP ══════════════════ */}
          <div className="lg:col-span-5 text-left space-y-6">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-6"
            >
              {/* Status Badge */}
              <motion.div variants={itemVariants} className="flex">
                <span className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-card/80 dark:bg-[#0D1117]/80 backdrop-blur-xl px-3.5 py-1.5 text-xs font-mono font-medium text-primary shadow-[0_0_15px_rgba(34,211,238,0.12)]">
                  <span className="flex h-2 w-2 rounded-full bg-[#2DD4A3] shadow-[0_0_8px_#2DD4A3] animate-pulse" />
                  v0.1.0-preview &nbsp;·&nbsp; Autonomous Agent Control Plane
                </span>
              </motion.div>

              {/* Main Headline */}
              <motion.h1
                variants={itemVariants}
                className="text-4xl sm:text-5xl md:text-[54px] font-extrabold tracking-tight text-foreground font-sans leading-[1.12]"
              >
                Build Software with{" "}
                <span className="inline-flex overflow-hidden">
                  {autonomousChars.map((ch, idx) => (
                    <motion.span
                      key={idx}
                      custom={idx}
                      variants={letterVariants}
                      className="inline-block text-transparent bg-clip-text bg-gradient-to-r from-[#22D3EE] via-[#67E8F9] to-[#2DD4A3] drop-shadow-[0_0_25px_rgba(34,211,238,0.3)]"
                    >
                      {ch}
                    </motion.span>
                  ))}
                </span>{" "}
                AI Agents
              </motion.h1>

              {/* Subheadline (Typing effect) */}
              <motion.div
                variants={itemVariants}
                className="text-sm sm:text-base leading-relaxed text-muted-foreground font-mono min-h-[50px] max-w-xl"
              >
                {typedTagline}
                <span className="inline-block w-[2px] h-[1em] ml-0.5 bg-[#22D3EE] animate-pulse align-middle" />
              </motion.div>

              {/* Primary & Secondary CTAs */}
              <motion.div
                variants={itemVariants}
                className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-1"
              >
                <Link href="/signup" className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    className="h-12 px-7 text-xs font-mono font-bold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] transition-all duration-200 w-full group rounded-xl"
                  >
                    <span>Deploy Control Plane</span>
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>

                <Link
                  href="https://github.com/rounakkumarsah/ASEP"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full sm:w-auto"
                >
                  <Button
                    size="lg"
                    variant="outline"
                    className="h-12 px-6 text-xs font-mono font-medium border-border/80 bg-card/60 backdrop-blur-md text-foreground hover:bg-accent hover:border-primary/40 transition-all duration-200 w-full rounded-xl"
                  >
                    <Github className="mr-2 h-4 w-4" />
                    GitHub Source
                  </Button>
                </Link>

                <Link href="/documentation" className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    variant="ghost"
                    className="h-12 px-4 text-xs font-mono font-medium text-muted-foreground hover:text-foreground hover:bg-accent/60 transition-all duration-200 w-full rounded-xl"
                  >
                    <BookOpen className="mr-2 h-4 w-4" />
                    Docs
                  </Button>
                </Link>
              </motion.div>

              {/* Trust Badges */}
              <motion.div variants={itemVariants} className="flex flex-wrap gap-2 pt-1">
                {[
                  { icon: Lock, label: "Zero-Trust Sandbox" },
                  { icon: Layers, label: "3-Layer Memory" },
                  { icon: Network, label: "MCP Native" },
                  { icon: ShieldCheck, label: "HITL Governance" },
                ].map(({ icon: Icon, label }) => (
                  <span
                    key={label}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border/70 bg-card/50 px-2.5 py-1 text-[11px] font-mono text-muted-foreground hover:border-primary/40 hover:text-primary transition-all duration-200"
                  >
                    <Icon className="h-3 w-3 text-primary" />
                    {label}
                  </span>
                ))}
              </motion.div>

              {/* Live Status Ticker */}
              <motion.div variants={itemVariants} className="pt-1">
                <div className="flex items-center gap-3 py-2 px-3 rounded-xl border border-border/60 bg-card/40 dark:bg-[#0D1117]/40 backdrop-blur-xl overflow-hidden shadow-inner">
                  <Marquee className="[--duration:28s]" pauseOnHover>
                    {[
                      ["Status", "OPERATIONAL", "#2DD4A3"],
                      ["Uptime SLA", "99.98%", "#F5F7FA"],
                      ["Sandboxes", "6 Active", "#22D3EE"],
                      ["Governance", "ENFORCED", "#2DD4A3"],
                      ["Latency", "<14ms", "#F5F7FA"],
                      ["Throughput", "1.2k req/s", "#22D3EE"],
                    ].map(([key, val, col]) => (
                      <span
                        key={key}
                        className="text-[10px] font-mono text-muted-foreground whitespace-nowrap mx-4"
                      >
                        {key}:{" "}
                        <span className="font-bold" style={{ color: col }}>
                          {val}
                        </span>
                      </span>
                    ))}
                  </Marquee>
                </div>
              </motion.div>
            </motion.div>
          </div>

          {/* ══════════════════ RIGHT COLUMN: LIVE INTERACTIVE PRODUCT DEMO ══════════════════ */}
          <div className="lg:col-span-7 w-full flex justify-center">
            <HeroProductDemo />
          </div>

        </div>
      </div>
    </section>
  );
}
