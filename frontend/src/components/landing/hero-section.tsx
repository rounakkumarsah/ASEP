"use client";

import React, { useEffect, useState, useRef } from "react";
import { motion, Variants, useScroll, useTransform } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  ArrowRight, Github, Terminal, Cpu,
  Activity, ShieldCheck, Database,
  Network, Lock, Layers,
} from "lucide-react";
import dynamic from "next/dynamic";
import { Spotlight } from "@/components/ui/spotlight";
import Marquee from "@/components/ui/marquee";

// Lazy load the heavy canvas visualization
const NeuralNetworkViz = dynamic(
  () => import("@/components/ui/neural-network-viz").then(m => m.NeuralNetworkViz),
  { ssr: false, loading: () => (
    <div className="w-full h-full flex items-center justify-center">
      <div className="h-12 w-12 rounded-full border-2 border-[#22D3EE]/30 border-t-[#22D3EE] animate-spin" />
    </div>
  )}
);

// ── Telemetry data ──────────────────────────────────────────────────────────
const LOGS_POOL = [
  "[PLANNER] Goal: 'Deploy microservice with full validation'",
  "[PLANNER] DAG decomposed — 4 parallel tasks identified",
  "[DOCKER] Spawning isolated sandbox workspace...",
  "[EXECUTOR] Source files cloned into sandbox",
  "[EXECUTOR] Running npm run lint — checking syntax",
  "[VERIFICATION] Lint passed. 0 warnings.",
  "[EXECUTOR] Running npx tsc --noEmit — type check",
  "[VERIFICATION] TypeScript: 0 errors, 0 warnings",
  "[EXECUTOR] npm run build — generating artifacts",
  "[VERIFICATION] Build complete in 3.42s. Exit 0",
  "[NEO4J] Writing execution trace to graph database",
  "[GOVERNANCE] Action signature verified. Policy OK.",
  "[MEMORY] Episodic context committed to vector store",
  "[TELEMETRY] All metrics nominal. 0 failures.",
  "[PLANNER] Next objective queued. Standby.",
];

const AGENT_EVENTS = [
  { agent: "PLANNER-01", action: "Deconstructed goal into 4 tasks", type: "plan" },
  { agent: "EXECUTOR-03", action: "Running lint in sandbox container", type: "exec" },
  { agent: "MEMORY-02", action: "Retrieved 12 relevant context chunks", type: "mem" },
  { agent: "GOVERNANCE", action: "Policy check passed — action approved", type: "gov" },
  { agent: "EVAL-01", action: "Scoring output quality: 94/100", type: "eval" },
  { agent: "MCP-TOOL", action: "GitHub PR #142 created successfully", type: "tool" },
];

const EVENT_COLORS: Record<string, string> = {
  plan: "#22D3EE",
  exec: "#67E8F9",
  mem:  "#2DD4A3",
  gov:  "#F5B942",
  eval: "#A78BFA",
  tool: "#34D399",
};

// ── Variants ─────────────────────────────────────────────────────────────────
const containerV: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.09, delayChildren: 0.1 } },
};
const itemV: Variants = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.25, 0.1, 0.25, 1] } },
};
const letterV: Variants = {
  hidden: { opacity: 0, y: 24, rotateX: -40 },
  visible: (i: number) => ({
    opacity: 1, y: 0, rotateX: 0,
    transition: { duration: 0.55, delay: i * 0.04, ease: [0.2, 0.8, 0.3, 1] },
  }),
};

// ── Component ─────────────────────────────────────────────────────────────────
export function HeroSection() {
  // Telemetry state
  const [logs, setLogs] = useState<string[]>([LOGS_POOL[0], LOGS_POOL[1]]);
  const [events, setEvents] = useState(AGENT_EVENTS.slice(0, 3));
  const [cpu, setCpu] = useState(17);
  const [mem, setMem] = useState(38);
  const [sessions, setSessions] = useState(6);
  const [logIdx, setLogIdx] = useState(2);
  const [eventIdx, setEventIdx] = useState(3);

  // Typing tagline
  const fullTagline = "Unify Planning, Execution, Memory, and Governance into a single production-grade control plane.";
  const [tagline, setTagline] = useState("");
  useEffect(() => {
    let i = 0;
    const t = setInterval(() => {
      setTagline(fullTagline.slice(0, i));
      i++;
      if (i > fullTagline.length) clearInterval(t);
    }, 18);
    return () => clearInterval(t);
  }, []);

  // Telemetry simulation
  useEffect(() => {
    const t = setInterval(() => {
      setLogs(prev => {
        const next = [...prev, LOGS_POOL[logIdx % LOGS_POOL.length]];
        return next.length > 16 ? next.slice(-16) : next;
      });
      setLogIdx(i => i + 1);

      setCpu(p => Math.max(10, Math.min(72, p + Math.floor(Math.random() * 9) - 4)));
      setMem(p => Math.max(32, Math.min(45, p + Math.floor(Math.random() * 3) - 1)));
      if (Math.random() > 0.75) {
        setSessions(p => Math.max(3, Math.min(14, p + (Math.random() > 0.5 ? 1 : -1))));
      }
      if (Math.random() > 0.6) {
        setEvents(prev => {
          const next = [AGENT_EVENTS[eventIdx % AGENT_EVENTS.length], ...prev];
          return next.slice(0, 5);
        });
        setEventIdx(i => i + 1);
      }
    }, 2600);
    return () => clearInterval(t);
  }, [logIdx, eventIdx]);

  // Scroll-linked parallax for the right column
  const heroRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const vizY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const vizOpacity = useTransform(scrollYProgress, [0, 0.6], [1, 0]);

  const autonomousLetters = "Autonomous".split("");

  return (
    <section
      ref={heroRef}
      id="hero"
      className="relative min-h-screen overflow-hidden bg-[#090B0F] pt-28 pb-0 border-b border-[#202833] flex flex-col selection:bg-[#22D3EE]/30"
    >
      {/* ── CSS animation keyframes ─── */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes panGrid { 0% { transform: translateY(0); } 100% { transform: translateY(4rem); } }
        @keyframes shimmer { 0%,100% { opacity:.05; } 50% { opacity:.12; } }
        .grid-pan { animation: panGrid 24s linear infinite; }
        .shimmer  { animation: shimmer 4s ease-in-out infinite; }
      ` }} />

      {/* ── Noise overlay ───────────────────────────────────────────────── */}
      <div
        className="pointer-events-none absolute inset-0 z-50 opacity-[0.035] mix-blend-overlay"
        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")` }}
      />

      {/* ── Moving grid ─────────────────────────────────────────────────── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-[-100%] grid-pan bg-[linear-gradient(to_right,#111720_1px,transparent_1px),linear-gradient(to_bottom,#111720_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] opacity-60" />
        <div className="absolute inset-0 bg-[#090B0F] [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,transparent_20%,#000_100%)]" />
      </div>

      {/* ── Radial glows ────────────────────────────────────────────────── */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-[#22D3EE]/8 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute top-1/2 right-0 w-[400px] h-[400px] bg-[#2DD4A3]/5 rounded-full blur-[120px] pointer-events-none" />
      <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="#22D3EE" />

      {/* ── Main grid ───────────────────────────────────────────────────── */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 w-full flex-1 flex flex-col">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16 items-center flex-1 py-8">

          {/* ══════════════════ LEFT COLUMN ══════════════════ */}
          <div className="lg:col-span-6 space-y-8 text-left">
            <motion.div
              variants={containerV}
              initial="hidden"
              animate="visible"
              className="space-y-7"
            >
              {/* Version badge */}
              <motion.div variants={itemV} className="flex">
                <span className="inline-flex items-center gap-2 rounded-full border border-[#202833]/80 bg-[#0D1117]/90 backdrop-blur-xl px-3.5 py-1.5 text-[11px] font-mono font-medium text-[#22D3EE] shadow-[0_0_20px_rgba(34,211,238,0.08)]">
                  <span className="flex h-1.5 w-1.5 rounded-full bg-[#2DD4A3] shadow-[0_0_8px_#2DD4A3] animate-pulse" />
                  v0.1.0-preview &nbsp;·&nbsp; Core Runtime Online
                </span>
              </motion.div>

              {/* Headline */}
              <motion.h1
                variants={itemV}
                className="text-5xl font-extrabold tracking-tight text-[#F5F7FA] sm:text-6xl md:text-[64px] font-sans leading-[1.1]"
                style={{ perspective: "800px" }}
              >
                {"Build Enterprise AI\nwith ".split("\n").map((line, li) => (
                  <span key={li} className="block">
                    {li === 0 ? (
                      line
                    ) : (
                      <>
                        {line}
                        <span className="inline-flex overflow-hidden" style={{ perspective: "400px" }}>
                          {autonomousLetters.map((ch, ci) => (
                            <motion.span
                              key={ci}
                              custom={ci}
                              variants={letterV}
                              className="inline-block text-transparent bg-clip-text bg-gradient-to-r from-[#22D3EE] via-[#67E8F9] to-[#2DD4A3]"
                              style={{ textShadow: "0 0 40px rgba(34,211,238,0.25)" }}
                            >
                              {ch}
                            </motion.span>
                          ))}
                        </span>{" "}
                        Agents
                      </>
                    )}
                  </span>
                ))}
              </motion.h1>

              {/* Subheadline: typing effect */}
              <motion.div
                variants={itemV}
                className="max-w-xl text-[15px] leading-relaxed text-[#9CA6B5] font-mono min-h-[56px]"
              >
                {tagline}
                <span className="inline-block w-[2px] h-[1em] ml-0.5 bg-[#22D3EE] animate-pulse align-middle" />
              </motion.div>

              {/* CTAs */}
              <motion.div
                variants={itemV}
                className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-1"
              >
                <Link href="/signup" className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    className="h-12 px-8 text-[13px] font-mono font-bold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] hover:shadow-[0_0_40px_-8px_rgba(34,211,238,0.7)] group w-full transition-all duration-300 relative overflow-hidden"
                  >
                    <span className="absolute inset-0 bg-gradient-to-r from-[#22D3EE] to-[#2DD4A3] opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <span className="relative flex items-center gap-2">
                      Deploy Control Plane
                      <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </span>
                  </Button>
                </Link>
                <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank" className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    variant="outline"
                    className="h-12 px-8 text-[13px] font-mono font-medium border-[#202833] bg-[#0D1117]/60 backdrop-blur-md text-[#F5F7FA] hover:bg-[#111720] hover:border-[#22D3EE]/40 hover:shadow-[0_0_20px_rgba(34,211,238,0.1)] w-full transition-all duration-300"
                  >
                    <Github className="mr-2 h-4 w-4" />
                    View on GitHub
                  </Button>
                </Link>
              </motion.div>

              {/* Trust pills */}
              <motion.div variants={itemV} className="flex flex-wrap gap-2 pt-1">
                {[
                  { icon: Lock,     label: "Zero Trust Execution" },
                  { icon: Layers,   label: "3-Layer Memory" },
                  { icon: Network,  label: "MCP Native" },
                  { icon: ShieldCheck, label: "Governance Enforced" },
                ].map(({ icon: Icon, label }) => (
                  <span
                    key={label}
                    className="inline-flex items-center gap-1.5 rounded-full border border-[#202833] bg-[#0D1117]/60 px-3 py-1 text-[10px] font-mono text-[#9CA6B5] hover:border-[#22D3EE]/30 hover:text-[#22D3EE] transition-all duration-200"
                  >
                    <Icon className="h-3 w-3" />
                    {label}
                  </span>
                ))}
              </motion.div>

              {/* Status ticker */}
              <motion.div variants={itemV}>
                <div className="flex items-center gap-3 py-2 px-3 rounded-xl border border-[#202833]/60 bg-[#0D1117]/40 backdrop-blur-xl overflow-hidden">
                  <Marquee className="[--duration:28s]" pauseOnHover>
                    {[
                      ["System Status", "OPERATIONAL", "#2DD4A3"],
                      ["Uptime", "99.98%", "#F5F7FA"],
                      ["Active Agents", `${sessions}`, "#22D3EE"],
                      ["Governance", "ENFORCED", "#2DD4A3"],
                      ["Avg Latency", "24ms", "#F5F7FA"],
                      ["Throughput", "1.2k req/s", "#22D3EE"],
                    ].map(([key, val, col]) => (
                      <span key={key} className="text-[10px] font-mono text-[#9CA6B5] whitespace-nowrap mx-5">
                        {key}:{" "}
                        <span className="font-bold" style={{ color: col }}>{val}</span>
                      </span>
                    ))}
                  </Marquee>
                </div>
              </motion.div>
            </motion.div>
          </div>

          {/* ══════════════════ RIGHT COLUMN ══════════════════ */}
          <motion.div
            className="lg:col-span-6 relative"
            style={{ y: vizY, opacity: vizOpacity }}
          >
            {/* Premium border frame */}
            <div className="relative rounded-2xl border border-[#202833]/60 bg-[#0D1117]/20 backdrop-blur-xl shadow-[0_0_80px_rgba(34,211,238,0.06)] overflow-hidden aspect-square">
              {/* Corner accents */}
              <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-[#22D3EE]/60 rounded-tl-2xl z-20 pointer-events-none" />
              <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-[#22D3EE]/60 rounded-tr-2xl z-20 pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-[#22D3EE]/60 rounded-bl-2xl z-20 pointer-events-none" />
              <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-[#22D3EE]/60 rounded-br-2xl z-20 pointer-events-none" />

              {/* Top header bar */}
              <div className="absolute top-0 inset-x-0 px-4 py-2.5 border-b border-[#202833]/60 bg-[#090B0F]/70 flex items-center justify-between z-20 pointer-events-none">
                <div className="flex items-center gap-2 text-[10px] font-mono text-[#667085]">
                  <Network className="h-3 w-3 text-[#22D3EE]" />
                  ASEP AGENT NETWORK
                </div>
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute h-full w-full rounded-full bg-[#2DD4A3] opacity-60" />
                    <span className="relative rounded-full h-2 w-2 bg-[#2DD4A3]" />
                  </span>
                  <span className="text-[9px] font-mono text-[#2DD4A3]">LIVE</span>
                  <span className="text-[9px] font-mono text-[#667085]">15 nodes · {sessions} active</span>
                </div>
              </div>

              {/* Neural network canvas */}
              <div className="absolute inset-0 pt-10">
                <NeuralNetworkViz className="w-full h-full" />
              </div>

              {/* Floating glassmorphism widgets */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8, duration: 0.6, type: "spring" }}
                className="absolute top-16 left-3 z-20 flex items-center gap-2.5 bg-[#090B0F]/75 backdrop-blur-xl border border-[#202833] rounded-xl px-3 py-2.5 shadow-[0_4px_24px_rgba(0,0,0,0.5),0_0_12px_rgba(34,211,238,0.08)] hover:border-[#22D3EE]/40 transition-all duration-300 max-w-[175px]"
              >
                <div className="p-2 rounded-lg bg-[#22D3EE]/10 border border-[#22D3EE]/20">
                  <Activity className="h-3.5 w-3.5 text-[#22D3EE]" />
                </div>
                <div>
                  <div className="text-[9px] font-mono text-[#667085] uppercase tracking-wider">SLA</div>
                  <div className="text-xs font-bold text-[#F5F7FA]">99.98% uptime</div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.95, duration: 0.6, type: "spring" }}
                className="absolute top-16 right-3 z-20 flex items-center gap-2.5 bg-[#090B0F]/75 backdrop-blur-xl border border-[#202833] rounded-xl px-3 py-2.5 shadow-[0_4px_24px_rgba(0,0,0,0.5),0_0_12px_rgba(45,212,163,0.08)] hover:border-[#2DD4A3]/40 transition-all duration-300"
              >
                <div className="p-2 rounded-lg bg-[#2DD4A3]/10 border border-[#2DD4A3]/20">
                  <ShieldCheck className="h-3.5 w-3.5 text-[#2DD4A3]" />
                </div>
                <div>
                  <div className="text-[9px] font-mono text-[#667085] uppercase tracking-wider">Governance</div>
                  <div className="text-xs font-bold text-[#F5F7FA]">Policy Locked</div>
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.1, duration: 0.6, type: "spring" }}
                className="absolute bottom-4 left-3 right-3 z-20 bg-[#090B0F]/85 backdrop-blur-xl border border-[#202833] rounded-xl px-4 py-2.5 shadow-[0_4px_24px_rgba(0,0,0,0.6)] flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute h-full w-full rounded-full bg-[#22D3EE] opacity-75" />
                    <span className="relative rounded-full h-2 w-2 bg-[#22D3EE]" />
                  </span>
                  <span className="text-[9px] font-mono text-[#9CA6B5]">ACTIVE TASK:</span>
                  <span className="text-[9px] font-mono text-[#F5F7FA] font-semibold truncate max-w-[120px]">Deploy microservice</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-mono text-[#2DD4A3] bg-[#2DD4A3]/10 px-1.5 py-0.5 rounded border border-[#2DD4A3]/20">EXECUTING</span>
                  <span className="text-[9px] font-mono text-[#667085]">24ms</span>
                </div>
              </motion.div>

              {/* Floating memory widget */}
              <motion.div
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.25, duration: 0.6, type: "spring" }}
                className="absolute bottom-20 right-3 z-20 flex items-center gap-2 bg-[#090B0F]/75 backdrop-blur-xl border border-[#202833] rounded-xl px-3 py-2 shadow-lg hover:border-[#67E8F9]/40 transition-all duration-300"
              >
                <div className="p-1.5 rounded-lg bg-[#67E8F9]/10 border border-[#67E8F9]/20">
                  <Database className="h-3 w-3 text-[#67E8F9]" />
                </div>
                <div>
                  <div className="text-[8px] font-mono text-[#667085]">GRAPH MEMORY</div>
                  <div className="text-[10px] font-bold text-[#F5F7FA]">Synced</div>
                </div>
              </motion.div>
            </div>

            {/* Hint label */}
            <p className="text-center text-[10px] font-mono text-[#667085] mt-3">
              Drag to rotate · Hover to inspect nodes
            </p>
          </motion.div>
        </div>

        {/* ══════════════ 3-PANEL TELEMETRY ══════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }}
          className="mt-12 pb-16"
        >
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">

            {/* Left: Terminal */}
            <div className="md:col-span-4 rounded-2xl border border-[#202833]/80 bg-[#090B0F]/80 backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col h-[300px] relative">
              <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#22D3EE]/60 to-transparent" />
              <div className="px-4 py-3 border-b border-[#202833]/50 flex items-center justify-between bg-[#0D1117]/50">
                <div className="flex items-center gap-2 text-[#9CA6B5]">
                  <Terminal className="h-3.5 w-3.5 text-[#22D3EE]" />
                  <span className="text-[10px] font-mono uppercase tracking-widest">sys.stdout</span>
                </div>
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#28C840]" />
                </div>
              </div>
              <div className="p-4 font-mono text-[10px] leading-relaxed overflow-y-auto flex-1 flex flex-col justify-end gap-1">
                {logs.map((log, i) => {
                  const isErr = log.includes("Error") || log.includes("failure");
                  const isOk  = log.includes("Success") || log.includes("complete") || log.includes("VERIFICATION") || log.includes("passed") || log.includes("nominal");
                  const col   = isErr ? "text-red-400" : isOk ? "text-[#2DD4A3]" : log.includes("[PLANNER]") ? "text-[#67E8F9]" : log.includes("[EXECUTOR]") ? "text-[#22D3EE]" : "text-[#667085]";
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -4 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex gap-2"
                    >
                      <span className="text-[#202833]">&gt;</span>
                      <span
                        className={col + " break-all"}
                        dangerouslySetInnerHTML={{
                          __html: log.replace(/\[(.*?)\]/g, '<span class="text-[#9CA6B5]">[$1]</span>'),
                        }}
                      />
                    </motion.div>
                  );
                })}
                <div className="flex gap-2 mt-0.5">
                  <span className="text-[#202833]">&gt;</span>
                  <span className="w-[6px] h-[10px] bg-[#22D3EE] animate-pulse" />
                </div>
              </div>
            </div>

            {/* Center: Agent Activity */}
            <div className="md:col-span-5 rounded-2xl border border-[#202833]/80 bg-[#090B0F]/80 backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col h-[300px] relative">
              <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#67E8F9]/60 to-transparent" />
              <div className="px-5 py-3.5 border-b border-[#202833]/50 flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#F5F7FA]">Agent Activity</span>
                <span className="text-[9px] font-mono text-[#22D3EE] bg-[#22D3EE]/10 px-2 py-0.5 rounded-full border border-[#22D3EE]/20 animate-pulse">LIVE</span>
              </div>
              <div className="p-4 overflow-y-auto space-y-2.5 flex-1">
                {events.map((ev, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex gap-3 items-start border border-[#202833]/50 rounded-xl p-3 bg-[#0D1117]/40 hover:bg-[#0D1117]/80 hover:border-[#202833] transition-colors cursor-default"
                  >
                    <div
                      className="mt-0.5 h-2 w-2 rounded-full flex-shrink-0 mt-1.5"
                      style={{ background: EVENT_COLORS[ev.type], boxShadow: `0 0 6px ${EVENT_COLORS[ev.type]}` }}
                    />
                    <div>
                      <div className="text-[9px] font-mono text-[#22D3EE] uppercase mb-0.5">{ev.agent}</div>
                      <div className="text-[10px] font-sans text-[#9CA6B5] leading-relaxed">{ev.action}</div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Right: Metrics */}
            <div className="md:col-span-3 rounded-2xl border border-[#202833]/80 bg-[#090B0F]/80 backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col h-[300px] relative">
              <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#2DD4A3]/60 to-transparent" />
              <div className="px-5 py-3.5 border-b border-[#202833]/50">
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#F5F7FA]">Node Metrics</span>
              </div>
              <div className="p-5 flex-1 flex flex-col justify-center gap-7">
                {[
                  { label: "CPU",      value: cpu,                  max: 100, icon: Cpu,      color: "#22D3EE" },
                  { label: "Memory",   value: mem,                  max: 100, icon: Database,  color: "#2DD4A3" },
                  { label: "Sessions", value: (sessions / 20) * 100, max: 100, icon: Activity, color: "#67E8F9", display: `${sessions}/20` },
                ].map(({ label, value, icon: Icon, color, display }) => (
                  <div key={label}>
                    <div className="flex justify-between text-[9px] font-mono text-[#9CA6B5] mb-2 uppercase tracking-wider">
                      <span className="flex items-center gap-1.5">
                        <Icon className="w-3 h-3" style={{ color }} />
                        {label}
                      </span>
                      <span style={{ color }}>{display ?? `${value}%`}</span>
                    </div>
                    <div className="h-1.5 bg-[#111720] rounded-full overflow-hidden">
                      <motion.div
                        className="h-full rounded-full"
                        animate={{ width: `${value}%` }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
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

      {/* ── Scroll indicator ─────────────────────────────────────────────── */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20">
        <motion.button
          animate={{ y: [0, 9, 0] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          className="flex flex-col items-center gap-1.5 text-[#667085] hover:text-[#22D3EE] transition-colors group cursor-pointer"
          onClick={() => window.scrollBy({ top: window.innerHeight * 0.85, behavior: "smooth" })}
        >
          <span className="text-[9px] font-mono uppercase tracking-[0.18em] group-hover:tracking-[0.22em] transition-all">
            Scroll
          </span>
          <div className="w-5 h-8 rounded-full border border-current flex items-start justify-center pt-1.5">
            <motion.div
              animate={{ y: [0, 10, 0], opacity: [1, 0, 1] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
              className="w-1 h-1 rounded-full bg-current"
            />
          </div>
        </motion.button>
      </div>
    </section>
  );
}
