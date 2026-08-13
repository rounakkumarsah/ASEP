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
  Activity,
  Terminal,
  Cpu,
  Database,
  MousePointer,
  Hand,
} from "lucide-react";
import dynamic from "next/dynamic";
import { Spotlight } from "@/components/ui/spotlight";
import Marquee from "@/components/ui/marquee";

// Lazy load the high-density 3D neural matrix visualization
const NeuralNetworkViz = dynamic(
  () => import("@/components/ui/neural-network-viz").then((m) => m.NeuralNetworkViz),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[300px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
          <span className="text-xs font-mono text-muted-foreground animate-pulse">
            Initializing 3D Neural Matrix...
          </span>
        </div>
      </div>
    ),
  }
);

// ── Telemetry Pool ───────────────────────────────────────────────────────────
const LOGS_POOL = [
  "[PLANNER] Goal received: 'Deploy microservice with isolated validation'",
  "[PLANNER] DAG decomposed — 4 parallel tasks generated",
  "[DOCKER] Spawning isolated sandbox workspace container...",
  "[EXECUTOR] Source files cloned into target sandbox",
  "[EXECUTOR] Running 'npm run lint' — validating syntax tree",
  "[VERIFICATION] Lint passed with 0 warnings",
  "[EXECUTOR] Running 'npx tsc --noEmit' — verifying strict types",
  "[VERIFICATION] TypeScript: 0 errors detected",
  "[EXECUTOR] 'npm run build' — generating optimized bundle",
  "[VERIFICATION] Build completed in 3.14s. Exit 0",
  "[NEO4J] Writing execution trace to knowledge graph",
  "[GOVERNANCE] Action signature verified. Zero policy violations.",
  "[MEMORY] Episodic context committed to vector store",
  "[TELEMETRY] All telemetry nominal. 0 failures recorded.",
  "[PLANNER] Standing by for next orchestration trigger.",
];

const AGENT_EVENTS = [
  { agent: "PLANNER-01", action: "Deconstructed goal into 4 parallel tasks", type: "plan" },
  { agent: "EXEC-DOCKER", action: "Spawned ephemeral container sandbox #248", type: "exec" },
  { agent: "MEM-GRAPH", action: "Indexed 18 context nodes in knowledge store", type: "mem" },
  { agent: "GOV-POLICY", action: "Cryptographic signature validated for task #248", type: "gov" },
  { agent: "EVAL-GUARD", action: "Safety evaluation complete: 100/100 pass score", type: "eval" },
  { agent: "MCP-GITHUB", action: "Pull Request #142 approved and tagged", type: "tool" },
];

const EVENT_COLORS: Record<string, string> = {
  plan: "#22D3EE",
  exec: "#2DD4A3",
  mem: "#67E8F9",
  gov: "#F5B942",
  eval: "#A78BFA",
  tool: "#34D399",
};

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

  // Telemetry simulation state
  const [logs, setLogs] = useState<string[]>([LOGS_POOL[0], LOGS_POOL[1]]);
  const [events, setEvents] = useState(AGENT_EVENTS.slice(0, 3));
  const [cpu, setCpu] = useState(16);
  const [mem, setMem] = useState(37);
  const [sessions, setSessions] = useState(6);
  const [logIdx, setLogIdx] = useState(2);
  const [eventIdx, setEventIdx] = useState(3);

  useEffect(() => {
    let index = 0;
    const timer = setInterval(() => {
      setTypedTagline(fullTagline.slice(0, index));
      index++;
      if (index > fullTagline.length) clearInterval(timer);
    }, 14);
    return () => clearInterval(timer);
  }, []);

  // Live telemetry streaming interval
  useEffect(() => {
    const t = setInterval(() => {
      setLogs((prev) => {
        const next = [...prev, LOGS_POOL[logIdx % LOGS_POOL.length]];
        return next.length > 16 ? next.slice(-16) : next;
      });
      setLogIdx((i) => i + 1);

      setCpu((p) => Math.max(12, Math.min(68, p + Math.floor(Math.random() * 9) - 4)));
      setMem((p) => Math.max(34, Math.min(46, p + Math.floor(Math.random() * 3) - 1)));
      if (Math.random() > 0.7) {
        setSessions((p) => Math.max(4, Math.min(12, p + (Math.random() > 0.5 ? 1 : -1))));
      }
      if (Math.random() > 0.5) {
        setEvents((prev) => {
          const next = [AGENT_EVENTS[eventIdx % AGENT_EVENTS.length], ...prev];
          return next.slice(0, 5);
        });
        setEventIdx((i) => i + 1);
      }
    }, 2400);

    return () => clearInterval(t);
  }, [logIdx, eventIdx]);

  return (
    <section
      id="hero"
      className="relative min-h-screen overflow-x-hidden bg-background dark:bg-[#090B0F] pt-24 sm:pt-28 md:pt-32 pb-14 sm:pb-20 border-b border-border transition-colors duration-300 flex flex-col justify-between"
    >
      {/* Background Decorative Grids */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-[-100%] bg-[linear-gradient(to_right,hsl(var(--border)/0.35)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.35)_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] opacity-35 dark:opacity-20" />
        <div className="absolute inset-0 bg-background/80 dark:bg-[#090B0F]/80 [mask-image:radial-gradient(ellipse_80%_60%_at_50%_0%,transparent_10%,black_100%)]" />
      </div>

      {/* Radiant Spotlights & Ambient Glows */}
      <div className="absolute top-10 left-1/4 w-[550px] h-[550px] bg-[#22D3EE]/10 dark:bg-[#22D3EE]/8 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute top-1/3 right-10 w-[450px] h-[450px] bg-[#2DD4A3]/10 dark:bg-[#2DD4A3]/6 rounded-full blur-[140px] pointer-events-none" />
      <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="#22D3EE" />

      {/* Main Hero Container */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 w-full flex-1 flex flex-col justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 xl:gap-14 items-center">
          
          {/* ══════════════════ LEFT COLUMN: VALUE PROP & CTAS ══════════════════ */}
          <div className="lg:col-span-6 text-center sm:text-left space-y-6">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-6"
            >
              {/* Status Badge */}
              <motion.div variants={itemVariants} className="flex justify-center sm:justify-start">
                <span className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-card/80 dark:bg-[#0D1117]/80 backdrop-blur-xl px-3.5 py-1.5 text-xs font-mono font-medium text-primary shadow-[0_0_15px_rgba(34,211,238,0.12)]">
                  <span className="flex h-2 w-2 rounded-full bg-[#2DD4A3] shadow-[0_0_8px_#2DD4A3] animate-pulse" />
                  v0.1.0-preview &nbsp;·&nbsp; Enterprise Agent Control Plane
                </span>
              </motion.div>

              {/* Main Headline */}
              <motion.h1
                variants={itemVariants}
                className="text-3xl sm:text-4xl md:text-5xl lg:text-[52px] xl:text-[56px] font-extrabold tracking-tight text-foreground font-sans leading-[1.12]"
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
                className="text-sm sm:text-base leading-relaxed text-muted-foreground font-mono min-h-[50px] max-w-xl mx-auto sm:mx-0"
              >
                {typedTagline}
                <span className="inline-block w-[2px] h-[1em] ml-0.5 bg-[#22D3EE] animate-pulse align-middle" />
              </motion.div>

              {/* Action Buttons */}
              <motion.div
                variants={itemVariants}
                className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-1 justify-center sm:justify-start"
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
              <motion.div variants={itemVariants} className="flex flex-wrap gap-2 pt-1 justify-center sm:justify-start">
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

              {/* Live Status Marquee */}
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

          {/* ══════════════════ RIGHT COLUMN: 3D NEURAL MATRIX ══════════════════ */}
          <div className="lg:col-span-6 w-full flex flex-col items-center justify-center">
            
            {/* Matrix Card Container (Fluid aspect ratio & responsive max width) */}
            <div className="relative w-full max-w-[420px] sm:max-w-[480px] md:max-w-[540px] lg:max-w-none aspect-square sm:aspect-[4/3] lg:aspect-square rounded-3xl border border-border/80 bg-card/40 dark:bg-[#0D1117]/30 backdrop-blur-2xl shadow-[0_0_80px_rgba(34,211,238,0.08)] overflow-hidden">
              
              {/* Corner Reticles */}
              <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-primary/70 rounded-tl-2xl z-20 pointer-events-none" />
              <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-primary/70 rounded-tr-2xl z-20 pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-primary/70 rounded-bl-2xl z-20 pointer-events-none" />
              <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-primary/70 rounded-br-2xl z-20 pointer-events-none" />

              {/* Top Status Header */}
              <div className="absolute top-0 inset-x-0 px-3.5 sm:px-4 py-2 sm:py-2.5 border-b border-border/60 bg-background/80 dark:bg-[#090B0F]/80 backdrop-blur-md flex items-center justify-between z-20 pointer-events-none">
                <div className="flex items-center gap-1.5 sm:gap-2 text-[10px] font-mono text-muted-foreground">
                  <Network className="h-3 w-3 text-primary" />
                  <span className="font-semibold text-foreground">ASEP NEURAL MATRIX</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute h-full w-full rounded-full bg-[#2DD4A3] opacity-75" />
                    <span className="relative rounded-full h-2 w-2 bg-[#2DD4A3]" />
                  </span>
                  <span className="text-[9px] font-mono font-bold text-[#2DD4A3]">LIVE 3D</span>
                  <span className="hidden sm:inline text-[9px] font-mono text-muted-foreground">24 nodes</span>
                </div>
              </div>

              {/* Fluid 3D Canvas */}
              <div className="absolute inset-0 pt-7 sm:pt-8 pb-9 sm:pb-10">
                <NeuralNetworkViz className="w-full h-full" />
              </div>

              {/* Floating SLA Badge */}
              <motion.div
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5, duration: 0.5, type: "spring" }}
                className="absolute top-12 sm:top-14 left-2.5 sm:left-3 z-20 flex items-center gap-2 bg-card/90 dark:bg-[#090B0F]/90 backdrop-blur-xl border border-border/80 rounded-xl px-2.5 sm:px-3 py-1.5 sm:py-2 shadow-xl hover:border-primary/50 transition-colors"
              >
                <div className="p-1 sm:p-1.5 rounded-lg bg-primary/10 border border-primary/20 text-primary">
                  <Activity className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                </div>
                <div>
                  <span className="text-[8px] sm:text-[9px] font-mono text-muted-foreground block uppercase">SLA</span>
                  <span className="text-[11px] sm:text-xs font-bold text-foreground">99.98% Uptime</span>
                </div>
              </motion.div>

              {/* Floating Security Badge */}
              <motion.div
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.65, duration: 0.5, type: "spring" }}
                className="absolute top-12 sm:top-14 right-2.5 sm:right-3 z-20 flex items-center gap-2 bg-card/90 dark:bg-[#090B0F]/90 backdrop-blur-xl border border-border/80 rounded-xl px-2.5 sm:px-3 py-1.5 sm:py-2 shadow-xl hover:border-[#2DD4A3]/50 transition-colors"
              >
                <div className="p-1 sm:p-1.5 rounded-lg bg-[#2DD4A3]/10 border border-[#2DD4A3]/20 text-[#2DD4A3]">
                  <ShieldCheck className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                </div>
                <div>
                  <span className="text-[8px] sm:text-[9px] font-mono text-muted-foreground block uppercase">Security</span>
                  <span className="text-[11px] sm:text-xs font-bold text-foreground">Policy Enforced</span>
                </div>
              </motion.div>

              {/* Bottom Task Telemetry Strip */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.5, type: "spring" }}
                className="absolute bottom-2.5 sm:bottom-3 left-2.5 sm:left-3 right-2.5 sm:right-3 z-20 bg-card/95 dark:bg-[#090B0F]/95 backdrop-blur-xl border border-border/80 rounded-xl px-3 py-1.5 sm:py-2 shadow-2xl flex items-center justify-between"
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <span className="relative flex h-2 w-2 flex-shrink-0">
                    <span className="animate-ping absolute h-full w-full rounded-full bg-primary opacity-75" />
                    <span className="relative rounded-full h-2 w-2 bg-primary" />
                  </span>
                  <span className="text-[9px] font-mono text-muted-foreground flex-shrink-0">TASK:</span>
                  <span className="text-[9px] font-mono font-semibold text-foreground truncate max-w-[130px] sm:max-w-[200px]">
                    Deploy microservice #248
                  </span>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span className="text-[9px] font-mono font-bold text-[#2DD4A3] bg-[#2DD4A3]/10 px-1.5 py-0.5 rounded border border-[#2DD4A3]/20">
                    ISOLATED
                  </span>
                  <span className="text-[9px] font-mono text-muted-foreground">14ms</span>
                </div>
              </motion.div>
            </div>

            {/* ── Instruction Text (Strictly BELOW the Neural Matrix Card) ─── */}
            <div className="mt-4 mb-2 flex items-center justify-center gap-2.5 text-xs font-mono text-muted-foreground/80 w-full max-w-[420px] sm:max-w-[480px] md:max-w-[540px] lg:max-w-none text-center">
              <span className="inline-flex items-center gap-1.5">
                <MousePointer className="w-3.5 h-3.5 text-primary" />
                <span>Drag to rotate</span>
              </span>
              <span className="text-border">•</span>
              <span className="inline-flex items-center gap-1.5">
                <Hand className="w-3.5 h-3.5 text-primary" />
                <span>Hover nodes for telemetry</span>
              </span>
            </div>

          </div>

        </div>

        {/* ══════════════════ 3-PANEL TELEMETRY FOOTER ══════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="mt-12 sm:mt-16"
        >
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            
            {/* 1. Terminal stdout */}
            <div className="md:col-span-5 rounded-2xl border border-border/80 bg-card/80 dark:bg-[#090B0F]/80 backdrop-blur-xl shadow-xl overflow-hidden flex flex-col h-[280px] relative">
              <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />
              <div className="px-4 py-2.5 border-b border-border/60 flex items-center justify-between bg-muted/40">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Terminal className="h-3.5 w-3.5 text-primary" />
                  <span className="text-[10px] font-mono uppercase tracking-widest text-foreground font-semibold">
                    sys.stdout
                  </span>
                </div>
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#28C840]" />
                </div>
              </div>
              <div className="p-3.5 font-mono text-[10px] leading-relaxed overflow-y-auto flex-1 flex flex-col justify-end gap-1 text-muted-foreground">
                {logs.map((log, i) => {
                  const isErr = log.includes("Error") || log.includes("failure");
                  const isOk =
                    log.includes("Success") ||
                    log.includes("complete") ||
                    log.includes("VERIFICATION") ||
                    log.includes("passed") ||
                    log.includes("nominal");
                  const col = isErr
                    ? "text-red-400"
                    : isOk
                    ? "text-[#2DD4A3]"
                    : log.includes("[PLANNER]")
                    ? "text-[#67E8F9]"
                    : log.includes("[EXECUTOR]")
                    ? "text-[#22D3EE]"
                    : "text-muted-foreground";

                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -4 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex gap-2"
                    >
                      <span className="text-border">&gt;</span>
                      <span
                        className={col + " break-all"}
                        dangerouslySetInnerHTML={{
                          __html: log.replace(
                            /\[(.*?)\]/g,
                            '<span class="text-foreground/80 font-bold">[$1]</span>'
                          ),
                        }}
                      />
                    </motion.div>
                  );
                })}
                <div className="flex gap-2 mt-0.5">
                  <span className="text-border">&gt;</span>
                  <span className="w-[6px] h-[10px] bg-primary animate-pulse" />
                </div>
              </div>
            </div>

            {/* 2. Agent Activity Feed */}
            <div className="md:col-span-4 rounded-2xl border border-border/80 bg-card/80 dark:bg-[#090B0F]/80 backdrop-blur-xl shadow-xl overflow-hidden flex flex-col h-[280px] relative">
              <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#67E8F9]/60 to-transparent" />
              <div className="px-4 py-2.5 border-b border-border/60 flex items-center justify-between bg-muted/40">
                <span className="text-[10px] font-mono uppercase tracking-widest text-foreground font-semibold">
                  Agent Activity
                </span>
                <span className="text-[9px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20 animate-pulse font-bold">
                  STREAMING
                </span>
              </div>
              <div className="p-3.5 overflow-y-auto space-y-2 flex-1">
                {events.map((ev, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.04 }}
                    className="flex gap-2.5 items-start border border-border/60 rounded-xl p-2.5 bg-muted/20 hover:bg-muted/40 hover:border-border transition-colors cursor-default"
                  >
                    <div
                      className="mt-1 h-2 w-2 rounded-full flex-shrink-0"
                      style={{
                        background: EVENT_COLORS[ev.type],
                        boxShadow: `0 0 6px ${EVENT_COLORS[ev.type]}`,
                      }}
                    />
                    <div>
                      <div className="text-[9px] font-mono text-primary font-semibold uppercase">
                        {ev.agent}
                      </div>
                      <div className="text-[10px] font-sans text-muted-foreground leading-snug">
                        {ev.action}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* 3. Node Telemetry Gauges */}
            <div className="md:col-span-3 rounded-2xl border border-border/80 bg-card/80 dark:bg-[#090B0F]/80 backdrop-blur-xl shadow-xl overflow-hidden flex flex-col h-[280px] relative">
              <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#2DD4A3]/60 to-transparent" />
              <div className="px-4 py-2.5 border-b border-border/60 bg-muted/40">
                <span className="text-[10px] font-mono uppercase tracking-widest text-foreground font-semibold">
                  Cluster Metrics
                </span>
              </div>
              <div className="p-4 flex-1 flex flex-col justify-center gap-5">
                {[
                  { label: "CPU Compute", value: cpu, icon: Cpu, color: "#22D3EE" },
                  { label: "Memory Pool", value: mem, icon: Database, color: "#2DD4A3" },
                  {
                    label: "Active Sandboxes",
                    value: (sessions / 12) * 100,
                    icon: Activity,
                    color: "#67E8F9",
                    display: `${sessions} / 12`,
                  },
                ].map(({ label, value, icon: Icon, color, display }) => (
                  <div key={label}>
                    <div className="flex justify-between text-[9px] font-mono text-muted-foreground mb-1.5 uppercase tracking-wider">
                      <span className="flex items-center gap-1.5">
                        <Icon className="w-3 h-3" style={{ color }} />
                        {label}
                      </span>
                      <span className="font-bold text-foreground">{display ?? `${value}%`}</span>
                    </div>
                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        className="h-full rounded-full"
                        animate={{ width: `${value}%` }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                        style={{
                          background: color,
                          boxShadow: `0 0 8px ${color}80`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </motion.div>
      </div>
    </section>
  );
}
